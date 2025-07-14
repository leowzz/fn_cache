import asyncio
import hashlib
import inspect
import json
import time
import threading
import sys
from functools import wraps
from typing import (
    Any,
    Callable,
    Optional,
    Iterable,
    AsyncIterable,
    AsyncGenerator,
    Dict,
    List,
)
from pydantic import BaseModel

from .config import CacheConfig, DEFAULT_PREFIX
from .enums import CacheType, StorageType, CacheKeyEnum, SerializerType
from .manager import UniversalCacheManager
from .utils import strify
from .utils.statistics import (
    get_cache_statistics as _get_cache_statistics,
    reset_cache_statistics as _reset_cache_statistics,
    CacheStatistics,
    record_cache_hit,
    record_cache_miss,
    record_cache_set,
    record_cache_delete,
    record_cache_error,
)
from loguru import logger


class MemoryUsageInfo(BaseModel):
    """内存使用信息"""

    manager_id: str
    storage_type: StorageType
    cache_type: CacheType
    item_count: int
    memory_bytes: int
    memory_mb: float
    max_size: int
    prefix: str


class _CacheRegistry:
    """
    内部缓存注册表，用于跟踪所有可预加载的缓存函数。
    支持定期计算所有缓存管理对象的内存占用情况。
    """

    def __init__(self):
        self._preload_able_funcs = []
        self._registered_managers: Dict[str, UniversalCacheManager] = {}
        self._monitoring_task: Optional[asyncio.Task] = None
        self._monitoring_interval: int = 300  # 默认5分钟监控一次
        self._monitoring_enabled: bool = False

    def __contains__(self, manager_id: str) -> bool:
        return manager_id in self._registered_managers

    def register(self, preload_info: dict):
        """注册一个可预加载的函数及其配置。"""
        self._preload_able_funcs.append(preload_info)

        # 同时注册缓存管理器
        manager = preload_info["manager"]
        manager_id = (
            f"{manager.config.storage_type.value}_{manager.config.prefix}_{id(manager)}"
        )
        self._registered_managers[manager_id] = manager

    def register_manager(
        self, manager: UniversalCacheManager, manager_id: Optional[str] = None
    ):
        """注册一个缓存管理器用于内存监控"""
        if manager_id in self:
            logger.debug(f"Cache manager {manager_id} already registered")
            return

        if manager_id is None:
            manager_id = f"{manager.config.storage_type.value}_{manager.config.prefix}_{id(manager)}"
        self._registered_managers[manager_id] = manager
        logger.debug(f"Registered cache manager for monitoring: {manager_id}")

    def unregister_manager(self, manager_id: str):
        """注销一个缓存管理器"""
        if manager_id in self._registered_managers:
            del self._registered_managers[manager_id]
            logger.info(f"Unregistered cache manager: {manager_id}")

    def get_memory_usage(self) -> List[MemoryUsageInfo]:
        """
        计算所有注册的缓存管理器的内存占用情况

        :return: 内存使用信息列表
        """
        memory_info_list = []

        for manager_id, manager in self._registered_managers.items():
            try:
                memory_info = self._calculate_manager_memory_usage(manager_id, manager)
                if memory_info:
                    memory_info_list.append(memory_info)
            except Exception as e:
                logger.error(
                    f"Error calculating memory usage for manager {manager_id}: {e}"
                )

        return memory_info_list

    def _calculate_manager_memory_usage(
        self, manager_id: str, manager: UniversalCacheManager
    ) -> Optional[MemoryUsageInfo]:
        """
        计算单个缓存管理器的内存占用

        :param manager_id: 管理器ID
        :param manager: 缓存管理器实例
        :return: 内存使用信息
        """
        if manager.config.storage_type != StorageType.MEMORY:
            # 非内存存储，无法准确计算内存占用
            return MemoryUsageInfo(
                manager_id=manager_id,
                storage_type=manager.config.storage_type,
                cache_type=manager.config.cache_type,
                item_count=0,
                memory_bytes=0,
                memory_mb=0.0,
                max_size=manager.config.max_size,
                prefix=manager.config.prefix,
            )

        # 获取内存存储实例
        storage = manager._storage
        if not hasattr(storage, "_cache"):
            return None

        cache = storage._cache
        item_count = len(cache)

        # 计算内存占用
        memory_bytes = self._estimate_cache_memory_usage(cache)
        memory_mb = memory_bytes / (1024 * 1024)

        return MemoryUsageInfo(
            manager_id=manager_id,
            storage_type=manager.config.storage_type,
            cache_type=manager.config.cache_type,
            item_count=item_count,
            memory_bytes=memory_bytes,
            memory_mb=memory_mb,
            max_size=manager.config.max_size,
            prefix=manager.config.prefix,
        )

    def _estimate_cache_memory_usage(self, cache: Dict) -> int:
        """
        估算缓存字典的内存占用

        :param cache: 缓存字典
        :return: 估算的内存字节数
        """
        total_size = 0

        # 基础字典开销
        total_size += sys.getsizeof(cache)

        for key, value in cache.items():
            # 键的大小
            total_size += sys.getsizeof(key)

            # 值的大小
            if isinstance(value, tuple):
                # TTL缓存：(value, expire_time)
                total_size += sys.getsizeof(value)
                if len(value) >= 1:
                    total_size += self._estimate_object_size(value[0])
                if len(value) >= 2:
                    total_size += sys.getsizeof(value[1])  # float
            else:
                # LRU缓存：直接存储值
                total_size += self._estimate_object_size(value)

        return total_size

    def _estimate_object_size(self, obj: Any) -> int:
        """
        估算对象的内存大小

        :param obj: 要估算的对象
        :return: 估算的内存字节数
        """
        if obj is None:
            return 0

        # 基础对象大小
        size = sys.getsizeof(obj)

        # 递归计算容器类型
        if isinstance(obj, (list, tuple, set)):
            size += sum(self._estimate_object_size(item) for item in obj)
        elif isinstance(obj, dict):
            size += sum(
                self._estimate_object_size(k) + self._estimate_object_size(v)
                for k, v in obj.items()
            )
        elif isinstance(obj, str):
            # 字符串已经包含在 sys.getsizeof 中
            pass
        elif hasattr(obj, "__dict__"):
            # 自定义对象
            size += self._estimate_object_size(obj.__dict__)

        return size

    def start_memory_monitoring(self, interval_seconds: int = 300):
        """
        启动内存监控

        :param interval_seconds: 监控间隔（秒）
        """
        if self._monitoring_enabled:
            logger.warning("Memory monitoring is already running")
            return

        self._monitoring_interval = interval_seconds
        self._monitoring_enabled = True

        if self._monitoring_task is None or self._monitoring_task.done():
            self._monitoring_task = asyncio.create_task(self._memory_monitoring_loop())
            logger.info(f"Started memory monitoring with {interval_seconds}s interval")

    def stop_memory_monitoring(self):
        """停止内存监控"""
        if not self._monitoring_enabled:
            return

        self._monitoring_enabled = False
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
        logger.info("Stopped memory monitoring")

    async def _memory_monitoring_loop(self):
        """内存监控循环"""
        while self._monitoring_enabled:
            try:
                await asyncio.sleep(self._monitoring_interval)
                if self._monitoring_enabled:
                    await self._log_memory_usage()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in memory monitoring loop: {e}")

    async def _log_memory_usage(self):
        """记录内存使用情况"""
        memory_info_list = self.get_memory_usage()

        if not memory_info_list:
            logger.info("No cache managers registered for memory monitoring")
            return

        total_memory_mb = sum(info.memory_mb for info in memory_info_list)
        total_items = sum(info.item_count for info in memory_info_list)

        logger.info(f"=== Cache Memory Usage Report ===")
        logger.info(f"Total managers: {len(memory_info_list)}")
        logger.info(f"Total items: {total_items}")
        logger.info(f"Total memory: {total_memory_mb:.2f} MB")

        for info in memory_info_list:
            if info.storage_type == StorageType.MEMORY:
                logger.info(
                    f"  {info.manager_id}: {info.item_count} items, "
                    f"{info.memory_mb:.2f} MB ({info.cache_type.value})"
                )
            else:
                logger.info(
                    f"  {info.manager_id}: {info.storage_type.value} storage "
                    f"(memory usage not available)"
                )

        logger.info("=== End Report ===")

    def get_memory_summary(self) -> Dict[str, Any]:
        """
        获取内存使用摘要

        :return: 内存使用摘要字典
        """
        memory_info_list = self.get_memory_usage()

        summary = {
            "total_managers": len(memory_info_list),
            "total_items": 0,
            "total_memory_mb": 0.0,
            "memory_storage_count": 0,
            "other_storage_count": 0,
            "managers": [],
        }

        for info in memory_info_list:
            summary["total_items"] += info.item_count
            summary["total_memory_mb"] += info.memory_mb

            if info.storage_type == StorageType.MEMORY:
                summary["memory_storage_count"] += 1
            else:
                summary["other_storage_count"] += 1

            summary["managers"].append(
                {
                    "manager_id": info.manager_id,
                    "storage_type": info.storage_type.value,
                    "cache_type": info.cache_type.value,
                    "item_count": info.item_count,
                    "memory_mb": info.memory_mb,
                    "max_size": info.max_size,
                    "prefix": info.prefix,
                }
            )

        return summary

    async def preload_all(self):
        """
        遍历所有已注册的函数，并为内存缓存执行预加载。
        """
        logger.info("Starting cache preloading...")
        for info in self._preload_able_funcs:
            manager: UniversalCacheManager = info["manager"]

            if manager.config.storage_type != StorageType.MEMORY:
                continue

            # 预加载时，我们总是希望填充缓存，因此不需要检查版本或开关
            # 预加载会使用当前的全局版本号

            key_builder = info["key_builder"]
            func = info["func"]
            preload_provider = info["preload_provider"]
            ttl_seconds = info["ttl_seconds"]

            try:
                call_params_iter: Iterable[tuple] = preload_provider()

                async for args, kwargs in self._iterate_params(call_params_iter):
                    result = await self._execute_func(func, *args, **kwargs)
                    if result is not None:
                        cache_key = key_builder(*args, **kwargs)
                        # set方法会自动使用当前的全局版本号
                        await manager.set(cache_key, result, ttl_seconds)
                        logger.info(f"Preloaded cache for {cache_key}")

            except Exception as e:
                logger.error(
                    f"Failed to preload cache for function {func.__name__}: {e}"
                )
        logger.info("Cache preloading finished.")

    @staticmethod
    async def _iterate_params(
        iterable: Iterable | AsyncIterable,
    ) -> AsyncGenerator[Any, Any]:
        if inspect.isasyncgen(iterable):
            async for item in iterable:
                yield item
        else:
            for item in iterable:
                yield item

    @staticmethod
    async def _execute_func(func: Callable, *args, **kwargs) -> Any:
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            # 在异步环境中运行同步函数
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


# 全局注册表实例
cache_registry = _CacheRegistry()


class cached:
    """
    通用轻量缓存装饰器类(Universal Light Cache)，支持丰富的配置选项和缓存预加载。
    支持自定义缓存键生成器，参考 aiocache 的设计模式。
    """

    def __init__(
        self,
        cache_type: CacheType = CacheType.TTL,
        storage_type: StorageType = StorageType.MEMORY,
        ttl_seconds: int = 60 * 10,  # 默认10分钟失效一次
        max_size: int = 1000,
        key_func: Optional[Callable] = None,
        prefix: str = DEFAULT_PREFIX,
        preload_provider: Optional[Callable[[], Iterable[tuple[tuple, dict]]]] = None,
        serializer_type: Optional[SerializerType] = None,
        serializer_kwargs: Optional[dict] = None,
        make_expire_sec_func: Optional[Callable] = None,
    ):
        """
        初始化缓存装饰器
        
        :param cache_type: 缓存类型 (TTL 或 LRU)
        :param storage_type: 存储类型 (MEMORY 或 REDIS)
        :param ttl_seconds: TTL缓存过期时间（秒）
        :param max_size: 最大缓存条目数
        :param key_func: 自定义缓存键生成函数，接收函数参数并返回缓存键字符串
        :param prefix: 缓存键前缀
        :param preload_provider: 预加载数据提供者
        :param serializer_type: 序列化类型
        :param serializer_kwargs: 序列化参数
        :param make_expire_sec_func: 动态过期时间计算函数
        """
        self.config = CacheConfig(
            cache_type=cache_type,
            storage_type=storage_type,
            ttl_seconds=ttl_seconds,
            max_size=max_size,
            prefix=prefix,
            serializer_type=serializer_type or SerializerType.JSON,
            serializer_kwargs=serializer_kwargs or {},
        )
        self.key_func = key_func
        self.preload_provider = preload_provider
        self.make_expire_sec_func = make_expire_sec_func
        
        # 检查是否使用默认配置，如果是则使用全局单例管理器
        is_default_config = (
            cache_type == CacheType.TTL and
            storage_type == StorageType.MEMORY and
            ttl_seconds == 60 * 10 and
            max_size == 1000 and
            prefix == DEFAULT_PREFIX and
            serializer_type is None and
            serializer_kwargs is None
        )
        
        if is_default_config:
            # 使用全局单例管理器
            self.cache_manager = _get_default_cache_manager()
        else:
            # 使用自定义配置创建新的管理器
            self.cache_manager = UniversalCacheManager(self.config)
            
        self._locks = {}  # key: threading.Lock or asyncio.Lock
        self._locks_lock = threading.Lock()

    def _get_lock(self, cache_key: str, is_async: bool):
        """
        获取全局唯一锁，保证同一个cache_key的锁对象唯一且线程安全。
        只有内存存储才需要锁，其他存储类型返回None。
        """
        if self.config.storage_type != StorageType.MEMORY:
            return None
            
        with self._locks_lock:
            lock = self._locks.get(cache_key)
            if lock is None:
                lock = asyncio.Lock() if is_async else threading.Lock()
                self._locks[cache_key] = lock
            return lock

    def _build_cache_key(
        self, func: Callable, args: tuple, kwargs: dict
    ) -> str:
        """
        构建缓存键
        
        :param func: 被装饰的函数
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 缓存键字符串
        """
        # 默认缓存键生成逻辑：模块名.函数名
        base_key = f"{func.__module__}.{func.__name__}"
        if self.key_func:
            # 使用自定义缓存键生成函数
            add_key = self.key_func(*args, **kwargs)
        else:
            add_key = f":{hash(strify((args, kwargs)))}"
        return f"{base_key}|{add_key}"

    def _parse_cached_value(self, cached_value: Any) -> Any:
        """解析缓存值"""
        if cached_value is None:
            return None

        # 如果缓存值是字符串，尝试解析为JSON
        if isinstance(cached_value, str):
            try:
                return json.loads(cached_value)
            except (json.JSONDecodeError, TypeError):
                return cached_value

        return cached_value

    def __call__(self, func: Callable) -> Callable:
        """返回包装后的函数，参考 aiocache 的设计模式"""
        # 自动注册缓存管理器到内存监控系统
        manager_id = f"{self.cache_manager.config.storage_type.value}_{self.cache_manager.config.prefix}_{id(self.cache_manager)}"
        cache_registry.register_manager(self.cache_manager, manager_id)

        if self.preload_provider:
            cache_registry.register(
                {
                    "func": func,
                    "manager": self.cache_manager,
                    "key_builder": lambda *args, **kwargs: self._build_cache_key(
                        func, args, kwargs
                    ),
                    "preload_provider": self.preload_provider,
                    "ttl_seconds": self.config.ttl_seconds,
                }
            )

        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                # 剥离控制参数，避免参与key构建
                cache_read = kwargs.pop('cache_read', True)
                cache_write = kwargs.pop('cache_write', True)
                wait_for_write = kwargs.pop('wait_for_write', True)
                return await self.decorator(
                    func, *args,
                    cache_read=cache_read,
                    cache_write=cache_write,
                    wait_for_write=wait_for_write,
                    **kwargs
                )
            
            # 将缓存管理器复制给装饰后的函数，便于后续调用 .cache.clear() 等方法
            wrapper.cache = self.cache_manager
            return wrapper
        else:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                # 剥离控制参数，避免参与key构建
                cache_read = kwargs.pop('cache_read', True)
                cache_write = kwargs.pop('cache_write', True)
                return self.decorator_sync(
                    func, *args,
                    cache_read=cache_read,
                    cache_write=cache_write,
                    **kwargs
                )
            
            # 将缓存管理器复制给装饰后的函数，便于后续调用 .cache.clear() 等方法
            wrapper.cache = self.cache_manager
            return wrapper

    async def decorator(
        self,
        func: Callable,
        *args,
        cache_read: bool = True,
        cache_write: bool = True,
        wait_for_write: bool = True,
        **kwargs,
    ) -> Any:
        """
        异步装饰器核心逻辑

        :param func: 被装饰的函数
        :param args: 位置参数
        :param cache_read: 是否读取缓存
        :param cache_write: 是否写入缓存
        :param wait_for_write: 是否等待写入完成
        :param kwargs: 关键字参数
        :return: 函数执行结果
        """
        return await self._decorator_common(
            func, args, kwargs,
            is_async=True,
            cache_read=cache_read,
            cache_write=cache_write,
            wait_for_write=wait_for_write
        )

    def decorator_sync(
        self,
        func: Callable,
        *args,
        cache_read: bool = True,
        cache_write: bool = True,
        **kwargs,
    ) -> Any:
        """
        同步装饰器核心逻辑

        :param func: 被装饰的函数
        :param args: 位置参数
        :param cache_read: 是否读取缓存
        :param cache_write: 是否写入缓存
        :param kwargs: 关键字参数
        :return: 函数执行结果
        """
        return self._decorator_common(
            func, args, kwargs,
            is_async=False,
            cache_read=cache_read,
            cache_write=cache_write
        )

    def _get_ttl(self, result):
        ttl_seconds = self.config.ttl_seconds
        if self.make_expire_sec_func:
            custom_ttl = self.make_expire_sec_func(result)
            if custom_ttl:
                ttl_seconds = custom_ttl
        return ttl_seconds

    def _decorator_common(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict,
        is_async: bool = False,
        cache_read: bool = True,
        cache_write: bool = True,
        wait_for_write: bool = True,
    ):
        """
        通用装饰器核心逻辑，支持同步和异步
        """
        # 检查全局缓存开关
        if not self.cache_manager.is_cache_enabled:
            if is_async:
                logger.info(f"Global cache disabled, skipping cache for {func.__name__}")
                return func(*args, **kwargs) if not asyncio.iscoroutinefunction(func) else asyncio.ensure_future(func(*args, **kwargs))
            else:
                return func(*args, **kwargs)

        start_time = time.perf_counter()
        cache_key = self._build_cache_key(func, args, kwargs)
        lock = self._get_lock(cache_key, is_async=is_async)

        async def async_inner():
            # 缓存读取逻辑
            if cache_read:
                cached = await self.cache_manager.get(cache_key)
                if cached is not None:
                    elapsed = time.perf_counter() - start_time
                    logger.info(f"Cache-hit: {cache_key} ({elapsed:.4f}s)")
                    # 记录缓存命中统计
                    record_cache_hit(self.cache_manager._storage.cache_id, elapsed)
                    return self._parse_cached_value(cached)
            # 执行原函数
            result = await func(*args, **kwargs)
            # 缓存写入逻辑
            if cache_write and result is not None:
                ttl_seconds = self._get_ttl(result)
                if wait_for_write:
                    await self.cache_manager.set(cache_key, result, ttl_seconds)
                else:
                    asyncio.create_task(self.cache_manager.set(cache_key, result, ttl_seconds))
            elapsed = time.perf_counter() - start_time
            logger.info(f"Cache-miss: {cache_key} ({elapsed:.4f}s)")
            # 记录缓存未命中统计
            record_cache_miss(self.cache_manager._storage.cache_id, elapsed)
            return result

        def sync_inner():
            if cache_read:
                cached = self._get_from_cache_sync(cache_key)
                if cached is not None:
                    elapsed = time.perf_counter() - start_time
                    logger.info(f"Cache-hit: {cache_key} ({elapsed:.4f}s)")
                    # 记录缓存命中统计
                    record_cache_hit(self.cache_manager._storage.cache_id, elapsed)
                    return self._parse_cached_value(cached)
            result = func(*args, **kwargs)
            if cache_write and result is not None:
                ttl_seconds = self._get_ttl(result)
                self._set_to_cache_sync(cache_key, result, ttl_seconds)
            elapsed = time.perf_counter() - start_time
            logger.info(f"Cache-miss: {cache_key} ({elapsed:.4f}s)")
            # 记录缓存未命中统计
            record_cache_miss(self.cache_manager._storage.cache_id, elapsed)
            return result

        if is_async:
            if lock:
                async def locked_async():
                    async with lock:
                        return await async_inner()
                return locked_async()
            else:
                return async_inner()
        else:
            if lock:
                with lock:
                    return sync_inner()
            else:
                return sync_inner()



    def _get_from_cache_sync(self, cache_key: str) -> Optional[Any]:
        """同步获取缓存"""
        try:
            return self.cache_manager.get_sync(cache_key)
        except ValueError:
            logger.debug(
                f"Cache-skip: {cache_key} (Redis storage not supported for sync operations)"
            )
            return None

    def _set_to_cache_sync(self, cache_key: str, result: Any, ttl_seconds: int):
        """同步设置缓存"""
        try:
            self.cache_manager.set_sync(cache_key, result, ttl_seconds)
        except ValueError:
            logger.warning(
                f"Cache-set-skip: {cache_key} (Redis storage not supported for sync operations)"
            )




async def preload_all_caches():
    """执行所有已注册的缓存预加载任务"""
    await cache_registry.preload_all()


async def invalidate_all_caches():
    """失效所有使用默认管理器的缓存"""
    default_manager = UniversalCacheManager()
    await default_manager.invalidate_all()





# 内存监控相关函数
def start_cache_memory_monitoring(interval_seconds: int = 300):
    """
    启动缓存内存监控

    :param interval_seconds: 监控间隔（秒），默认5分钟
    """

    cache_registry.start_memory_monitoring(interval_seconds)


def stop_cache_memory_monitoring():
    """停止缓存内存监控"""
    cache_registry.stop_memory_monitoring()


def get_cache_memory_usage() -> List[MemoryUsageInfo]:
    """
    获取所有缓存管理器的内存使用情况

    :return: 内存使用信息列表
    """
    return cache_registry.get_memory_usage()


def get_cache_memory_summary() -> Dict[str, Any]:
    """
    获取缓存内存使用摘要

    :return: 内存使用摘要字典
    """
    return cache_registry.get_memory_summary()


def register_cache_manager_for_monitoring(
    manager: UniversalCacheManager, manager_id: Optional[str] = None
):
    """
    注册缓存管理器用于内存监控

    :param manager: 缓存管理器实例
    :param manager_id: 可选的管理器ID，如果不提供则自动生成
    """
    cache_registry.register_manager(manager, manager_id)


def unregister_cache_manager_from_monitoring(manager_id: str):
    """
    从内存监控中注销缓存管理器

    :param manager_id: 管理器ID
    """
    cache_registry.unregister_manager(manager_id)


# 缓存统计相关函数
def get_cache_statistics(cache_id: Optional[str] = None) -> Dict[str, Any]:
    """
    获取缓存统计信息

    :param cache_id: 可选的缓存ID，如果不提供则返回所有缓存的统计信息
    :return: 缓存统计信息字典
    """
    return _get_cache_statistics(cache_id)


def reset_cache_statistics(cache_id: Optional[str] = None):
    """重置缓存统计信息"""
    _reset_cache_statistics(cache_id)


# 全局缓存控制函数
# 使用单例模式管理默认缓存管理器
_default_cache_manager = None

def _get_default_cache_manager() -> UniversalCacheManager:
    """获取默认缓存管理器单例"""
    global _default_cache_manager
    if _default_cache_manager is None:
        _default_cache_manager = UniversalCacheManager()
    return _default_cache_manager

def enable_global_cache():
    """
    启用全局缓存功能
    
    启用后，所有使用默认配置的缓存管理器将正常工作。
    注意：此函数只影响使用默认配置的缓存管理器，自定义配置的缓存管理器需要单独控制。
    """
    from .config import enable_global_cache as _enable_global_cache
    _enable_global_cache()
    logger.info("Global cache enabled for default manager")


def disable_global_cache():
    """
    禁用全局缓存功能
    
    禁用后，所有使用默认配置的缓存管理器将被忽略：
    - get操作返回None
    - set操作返回False
    - delete操作返回False
    - 装饰器直接执行原函数，跳过缓存逻辑
    
    注意：此函数只影响使用默认配置的缓存管理器，自定义配置的缓存管理器需要单独控制。
    """
    from .config import disable_global_cache as _disable_global_cache
    _disable_global_cache()
    logger.info("Global cache disabled for default manager")


def is_global_cache_enabled() -> bool:
    """
    检查全局缓存是否已启用
    
    :return: 是否启用
    """
    from .config import is_global_cache_enabled as _is_global_cache_enabled
    return _is_global_cache_enabled()


def enable_all_registered_caches():
    """
    启用所有已注册的缓存管理器
    
    此函数会遍历所有已注册到监控系统的缓存管理器，并启用它们的缓存功能。
    """
    from .config import enable_global_cache as _enable_global_cache
    _enable_global_cache()
    logger.info(f"Enabled all registered cache managers ({len(cache_registry._registered_managers)} managers)")


def disable_all_registered_caches():
    """
    禁用所有已注册的缓存管理器
    
    此函数会遍历所有已注册到监控系统的缓存管理器，并禁用它们的缓存功能。
    """
    from .config import disable_global_cache as _disable_global_cache
    _disable_global_cache()
    logger.info(f"Disabled all registered cache managers ({len(cache_registry._registered_managers)} managers)")


def get_all_cache_status() -> Dict[str, bool]:
    """
    获取所有已注册缓存管理器的状态
    
    :return: 管理器ID到启用状态的映射
    """
    from .config import is_global_cache_enabled as _is_global_cache_enabled
    status = {}
    global_status = _is_global_cache_enabled()
    for manager_id, manager in cache_registry._registered_managers.items():
        status[manager_id] = global_status
    return status
