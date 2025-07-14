import asyncio
import hashlib
import inspect
import json
import time
import threading
import sys
from functools import wraps
from typing import Any, Callable, Optional, Iterable, AsyncIterable, AsyncGenerator, Dict, List
from dataclasses import dataclass

from .config import CacheConfig, DEFAULT_PREFIX
from .enums import CacheType, StorageType, CacheKeyEnum
from .manager import UniversalCacheManager
from .utils import strify
from loguru import logger

@dataclass
class MemoryUsageInfo:
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
        manager = preload_info['manager']
        manager_id = f"{manager.config.storage_type.value}_{manager.config.prefix}_{id(manager)}"
        self._registered_managers[manager_id] = manager

    def register_manager(self, manager: UniversalCacheManager, manager_id: Optional[str] = None):
        """注册一个缓存管理器用于内存监控"""
        if manager_id in self:
            logger.debug(f"Cache manager {manager_id} already registered")
            return
        
        if manager_id is None:
            manager_id = f"{manager.config.storage_type.value}_{manager.config.prefix}_{id(manager)}"
        self._registered_managers[manager_id] = manager
        logger.info(f"Registered cache manager for monitoring: {manager_id}")

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
                logger.error(f"Error calculating memory usage for manager {manager_id}: {e}")
        
        return memory_info_list

    def _calculate_manager_memory_usage(self, manager_id: str, manager: UniversalCacheManager) -> Optional[MemoryUsageInfo]:
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
                prefix=manager.config.prefix
            )
        
        # 获取内存存储实例
        storage = manager._storage
        if not hasattr(storage, '_cache'):
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
            prefix=manager.config.prefix
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
            size += sum(self._estimate_object_size(k) + self._estimate_object_size(v) 
                       for k, v in obj.items())
        elif isinstance(obj, str):
            # 字符串已经包含在 sys.getsizeof 中
            pass
        elif hasattr(obj, '__dict__'):
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
                logger.info(f"  {info.manager_id}: {info.item_count} items, "
                          f"{info.memory_mb:.2f} MB ({info.cache_type.value})")
            else:
                logger.info(f"  {info.manager_id}: {info.storage_type.value} storage "
                          f"(memory usage not available)")
        
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
            "managers": []
        }
        
        for info in memory_info_list:
            summary["total_items"] += info.item_count
            summary["total_memory_mb"] += info.memory_mb
            
            if info.storage_type == StorageType.MEMORY:
                summary["memory_storage_count"] += 1
            else:
                summary["other_storage_count"] += 1
            
            summary["managers"].append({
                "manager_id": info.manager_id,
                "storage_type": info.storage_type.value,
                "cache_type": info.cache_type.value,
                "item_count": info.item_count,
                "memory_mb": info.memory_mb,
                "max_size": info.max_size,
                "prefix": info.prefix
            })
        
        return summary

    async def preload_all(self):
        """
        遍历所有已注册的函数，并为内存缓存执行预加载。
        """
        logger.info("Starting cache preloading...")
        for info in self._preload_able_funcs:
            manager: UniversalCacheManager = info['manager']

            if manager.config.storage_type != StorageType.MEMORY:
                continue

            # 预加载时，我们总是希望填充缓存，因此不需要检查版本或开关
            # 预加载会使用当前的全局版本号

            key_builder = info['key_builder']
            func = info['func']
            preload_provider = info['preload_provider']
            ttl_seconds = info['ttl_seconds']

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
                logger.error(f"Failed to preload cache for function {func.__name__}: {e}")
        logger.info("Cache preloading finished.")

    @staticmethod
    async def _iterate_params(iterable: Iterable | AsyncIterable) -> AsyncGenerator[Any, Any]:
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


class u_l_cache:
    """
    通用轻量缓存装饰器类(Universal Light Cache)，支持丰富的配置选项和缓存预加载。

    使用方法:
    1. 在函数上添加装饰器
    2. 可选: 使用预加载功能
    3. 可选: 使用全局缓存失效功能
    4. 可选: 使用缓存预加载功能
    """

    def __init__(
            self,
            cache_type: CacheType = CacheType.TTL,
            storage_type: StorageType = StorageType.MEMORY,
            ttl_seconds: int = 60 * 10,  # 默认10分钟失效一次
            max_size: int = 1000,
            key_func: Optional[Callable] = None,
            key_params: Optional[list[str]] = None,
            prefix: str = DEFAULT_PREFIX,
            preload_provider: Optional[Callable[[], Iterable[tuple[tuple, dict]]]] = None
    ):
        """
        :param preload_provider: 一个函数，返回一个可迭代对象，
                                 用于提供预加载所需的参数，格式为 (args, kwargs) 的元组。
                                 例如: lambda: [((1,), {}), ((2,), {})]
        """
        self.config = CacheConfig(
            cache_type=cache_type, storage_type=storage_type,
            ttl_seconds=ttl_seconds, max_size=max_size, prefix=prefix
        )
        self.key_func = key_func
        self.key_params = key_params
        self.preload_provider = preload_provider
        self.cache_manager = UniversalCacheManager(self.config)
        self._locks = {}  # key: threading.Lock or asyncio.Lock
        self._locks_lock = threading.Lock()

    @classmethod
    def make_ctx_cache_sign(cls):
        """生成上下文缓存签名（简化版本）"""
        # 简化版本，不依赖外部上下文
        return hashlib.md5("default_context".encode()).hexdigest()

    def _get_lock(self, cache_key: str, is_async: bool):
        if self.config.storage_type != StorageType.MEMORY:
            return None
        with self._locks_lock:
            if cache_key not in self._locks:
                self._locks[cache_key] = asyncio.Lock() if is_async else threading.Lock()
            return self._locks[cache_key]

    def __call__(self, func: Callable) -> Callable:

        # 自动注册缓存管理器到内存监控系统
        manager_id = f"{self.cache_manager.config.storage_type.value}_{self.cache_manager.config.prefix}_{id(self.cache_manager)}"
        cache_registry.register_manager(self.cache_manager, manager_id)

        def build_cache_key(*args, **kwargs) -> str:
            if self.key_func:
                return self.key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__module__}.{func.__name__}"
                if self.key_params:
                    sig = inspect.signature(func)
                    bound_args = sig.bind(*args, **kwargs)
                    bound_args.apply_defaults()

                    key_values = [
                        f"{param}={bound_args.arguments[param]}"
                        for param in self.key_params if param in bound_args.arguments
                    ]
                    if key_values:
                        cache_key += ":" + ":".join(key_values)
                    else:
                        cache_key += f":{hash(strify((args, kwargs)))}"
                else:
                    cache_key += f":{hash(strify((args, kwargs)))}"
                addition_cache_k = self.make_ctx_cache_sign()

                return f"{cache_key}:{addition_cache_k[:8]}"

        if self.preload_provider:
            cache_registry.register({
                'func': func,
                'manager': self.cache_manager,
                'key_builder': build_cache_key,
                'preload_provider': self.preload_provider,
                'ttl_seconds': self.config.ttl_seconds,
            })

        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                start_time = time.perf_counter()
                cache_key = build_cache_key(*args, **kwargs)
                lock = self._get_lock(cache_key, is_async=True)
                if lock:
                    async with lock:
                        cached = await self.cache_manager.get(cache_key)
                        if cached is not None:
                            elapsed = time.perf_counter() - start_time
                            logger.info(f"Cache-hit: {cache_key} ({elapsed:.4f}s)")
                            return cached
                        result = await func(*args, **kwargs)
                        if result is not None:
                            await self.cache_manager.set(cache_key, result, self.config.ttl_seconds)
                        elapsed = time.perf_counter() - start_time
                        logger.info(f"Cache-miss: {cache_key} ({elapsed:.4f}s)")
                        return result
                else:
                    cached = await self.cache_manager.get(cache_key)
                    if cached is not None:
                        elapsed = time.perf_counter() - start_time
                        logger.info(f"Cache-hit: {cache_key} ({elapsed:.4f}s)")
                        return cached
                    result = await func(*args, **kwargs)
                    if result is not None:
                        await self.cache_manager.set(cache_key, result, self.config.ttl_seconds)
                    elapsed = time.perf_counter() - start_time
                    logger.info(f"Cache-miss: {cache_key} ({elapsed:.4f}s)")
                    return result

            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                start_time = time.perf_counter()
                cache_key = build_cache_key(*args, **kwargs)
                lock = self._get_lock(cache_key, is_async=False)
                if lock:
                    with lock:
                        cached = None
                        try:
                            cached = self.cache_manager.get_sync(cache_key)
                        except ValueError:
                            logger.info(f"Cache-skip: {cache_key} (Redis storage not supported for sync operations)")
                            pass
                        if cached is not None:
                            elapsed = time.perf_counter() - start_time
                            logger.info(f"Cache-hit: {cache_key} ({elapsed:.4f}s)")
                            return cached
                        result = func(*args, **kwargs)
                        if result is not None:
                            try:
                                self.cache_manager.set_sync(cache_key, result, self.config.ttl_seconds)
                            except ValueError:
                                logger.warning(f"Cache-set-skip: {cache_key} (Redis storage not supported for sync operations)")
                                pass
                        elapsed = time.perf_counter() - start_time
                        logger.info(f"Cache-miss: {cache_key} ({elapsed:.4f}s)")
                        return result
                else:
                    cached = None
                    try:
                        cached = self.cache_manager.get_sync(cache_key)
                    except ValueError:
                        logger.warning(f"Cache-skip: {cache_key} (Redis storage not supported for sync operations)")
                        pass
                    if cached is not None:
                        elapsed = time.perf_counter() - start_time
                        logger.info(f"Cache-hit: {cache_key} ({elapsed:.4f}s)")
                        return cached
                    result = func(*args, **kwargs)
                    if result is not None:
                        try:
                            self.cache_manager.set_sync(cache_key, result, self.config.ttl_seconds)
                        except ValueError:
                            logger.warning(f"Cache-set-skip: {cache_key} (Redis storage not supported for sync operations)")
                            pass
                    elapsed = time.perf_counter() - start_time
                    logger.info(f"Cache-miss: {cache_key} ({elapsed:.4f}s)")
                    return result
            return sync_wrapper


class l_user_cache:
    """
    基于缓存键枚举的装饰器，支持用户级别版本控制。
    """

    def __init__(
            self,
            cache_key: CacheKeyEnum,
            storage_type: StorageType = StorageType.REDIS,
            make_expire_sec_func: Optional[Callable] = None,
            key_params: Optional[list[str]] = None,
            prefix: str = DEFAULT_PREFIX,
            user_id_param: str = "user_id"
    ):
        self.cache_key = cache_key
        self.storage_type = storage_type
        self.make_expire_sec_func = make_expire_sec_func
        self.key_params = key_params if key_params is not None else None
        self.prefix = prefix
        self.user_id_param = user_id_param
        
        # 在初始化时创建缓存管理器实例，确保同一个装饰器实例使用同一个管理器
        config = CacheConfig(storage_type=self.storage_type, prefix=self.prefix)
        self.cache_manager = UniversalCacheManager(config)


    def __call__(self, func: Callable) -> Callable:

        def build_cache_key(args: tuple, kwargs: dict) -> tuple[str, Optional[str], bool]:
            """
            构建缓存键
            返回: (cache_key, user_id, is_user_cache)
            """
            sig = inspect.signature(func)
            bound_args = sig.bind_partial(*args, **kwargs)
            bound_args.apply_defaults()
            key_values = {}
            for param in (self.key_params or []):
                if param in bound_args.arguments:
                    key_values[param] = bound_args.arguments[param]
            # 兼容无key_params时的情况
            try:
                cache_key = self.cache_key.format(**key_values)
            except KeyError:
                cache_key = self.cache_key.value
            user_id = key_values.get(self.user_id_param) or kwargs.get(self.user_id_param) or None
            is_user_cache = self.user_id_param in key_values
            return cache_key, user_id, is_user_cache

        def parse_cached_value(cached_value: Any, return_type: Any) -> Any:
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

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            cache_key, user_id, is_user_cache = build_cache_key(args, kwargs)

            # 获取缓存
            cached = await self.cache_manager.get(cache_key, user_id=user_id)
            if cached is not None:
                return parse_cached_value(cached, None)

            # 执行函数
            result = await func(*args, **kwargs)

            # 计算过期时间
            ttl_seconds = None
            if self.make_expire_sec_func:
                ttl_seconds = self.make_expire_sec_func(result)

            # 存储到缓存
            if result is not None:
                await self.cache_manager.set(cache_key, result, ttl_seconds, user_id=user_id)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            cache_key, user_id, is_user_cache = build_cache_key(args, kwargs)

            # 获取缓存（仅支持内存存储的同步操作）
            if self.storage_type == StorageType.MEMORY:
                cached = self.cache_manager.get_sync(cache_key, user_id=user_id)
                if cached is not None:
                    return parse_cached_value(cached, None)

            # 执行函数
            result = func(*args, **kwargs)

            # 计算过期时间
            ttl_seconds = None
            if self.make_expire_sec_func:
                ttl_seconds = self.make_expire_sec_func(result)

            # 存储到缓存（仅支持内存存储的同步操作）
            if result is not None and self.storage_type == StorageType.MEMORY:
                self.cache_manager.set_sync(cache_key, result, ttl_seconds, user_id=user_id)

            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    @staticmethod
    async def invalidate_cache(
            user_id: str,
            cache_key_enum: CacheKeyEnum,
            key_params: Optional[dict] = None,
            prefix: str = DEFAULT_PREFIX,
            storage_type: StorageType = StorageType.REDIS
    ):
        """失效指定用户的指定缓存"""
        config = CacheConfig(storage_type=storage_type, prefix=prefix)
        manager = UniversalCacheManager(config)

        key_params = key_params or {}
        cache_key = cache_key_enum.format(**key_params)
        await manager.delete(cache_key)


async def preload_all_caches():
    """执行所有已注册的缓存预加载任务"""
    await cache_registry.preload_all()


async def invalidate_all_caches():
    """失效所有使用默认管理器的缓存"""
    default_manager = UniversalCacheManager()
    await default_manager.invalidate_all()


async def invalidate_user_cache(user_id: str):
    """使用户的所有缓存失效"""
    default_manager = UniversalCacheManager()
    await default_manager.invalidate_user_cache(user_id)


async def invalidate_user_key_cache(
        user_id: str,
        cache_key_enum: CacheKeyEnum,
        key_params: Optional[dict] = None,
        prefix: str = DEFAULT_PREFIX,
        storage_type: StorageType = StorageType.REDIS
):
    """失效指定用户的指定缓存键"""
    await l_user_cache.invalidate_cache(user_id, cache_key_enum, key_params, prefix, storage_type)


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


def register_cache_manager_for_monitoring(manager: UniversalCacheManager, manager_id: Optional[str] = None):
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
