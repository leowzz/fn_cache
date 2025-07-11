import asyncio
import hashlib
import inspect
import json
import time
from functools import wraps
from typing import Any, Callable, Optional, Iterable, AsyncIterable, AsyncGenerator
import threading

from .config import CacheConfig
from .enums import CacheType, StorageType, CacheKeyEnum
from .manager import UniversalCacheManager
from .utils import strify


class _CacheRegistry:
    """
    内部缓存注册表，用于跟踪所有可预加载的缓存函数。
    """

    def __init__(self):
        self._preload_able_funcs = []

    def register(self, preload_info: dict):
        """注册一个可预加载的函数及其配置。"""
        self._preload_able_funcs.append(preload_info)

    async def preload_all(self):
        """
        遍历所有已注册的函数，并为内存缓存执行预加载。
        """
        print("Starting cache preloading...")
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
                        print(f"Preloaded cache for {cache_key}")

            except Exception as e:
                print(f"Failed to preload cache for function {func.__name__}: {e}")
        print("Cache preloading finished.")

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

default_cache_registry = _CacheRegistry()


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
            prefix: str = "cache:",
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
            default_cache_registry.register({
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
                            print(f"Cache-hit: {cache_key} ({elapsed:.4f}s)")
                            return cached
                        result = await func(*args, **kwargs)
                        if result is not None:
                            await self.cache_manager.set(cache_key, result, self.config.ttl_seconds)
                        elapsed = time.perf_counter() - start_time
                        print(f"Cache-miss: {cache_key} ({elapsed:.4f}s)")
                        return result
                else:
                    cached = await self.cache_manager.get(cache_key)
                    if cached is not None:
                        elapsed = time.perf_counter() - start_time
                        print(f"Cache-hit: {cache_key} ({elapsed:.4f}s)")
                        return cached
                    result = await func(*args, **kwargs)
                    if result is not None:
                        await self.cache_manager.set(cache_key, result, self.config.ttl_seconds)
                    elapsed = time.perf_counter() - start_time
                    print(f"Cache-miss: {cache_key} ({elapsed:.4f}s)")
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
                            print(f"Cache-skip: {cache_key} (Redis storage not supported for sync operations)")
                            pass
                        if cached is not None:
                            elapsed = time.perf_counter() - start_time
                            print(f"Cache-hit: {cache_key} ({elapsed:.4f}s)")
                            return cached
                        result = func(*args, **kwargs)
                        if result is not None:
                            try:
                                self.cache_manager.set_sync(cache_key, result, self.config.ttl_seconds)
                            except ValueError:
                                print(f"Cache-set-skip: {cache_key} (Redis storage not supported for sync operations)")
                                pass
                        elapsed = time.perf_counter() - start_time
                        print(f"Cache-miss: {cache_key} ({elapsed:.4f}s)")
                        return result
                else:
                    cached = None
                    try:
                        cached = self.cache_manager.get_sync(cache_key)
                    except ValueError:
                        print(f"Cache-skip: {cache_key} (Redis storage not supported for sync operations)")
                        pass
                    if cached is not None:
                        elapsed = time.perf_counter() - start_time
                        print(f"Cache-hit: {cache_key} ({elapsed:.4f}s)")
                        return cached
                    result = func(*args, **kwargs)
                    if result is not None:
                        try:
                            self.cache_manager.set_sync(cache_key, result, self.config.ttl_seconds)
                        except ValueError:
                            print(f"Cache-set-skip: {cache_key} (Redis storage not supported for sync operations)")
                            pass
                    elapsed = time.perf_counter() - start_time
                    print(f"Cache-miss: {cache_key} ({elapsed:.4f}s)")
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
            prefix: str = "l_cache:",
            user_id_param: str = "user_id"
    ):
        self.cache_key = cache_key
        self.storage_type = storage_type
        self.make_expire_sec_func = make_expire_sec_func
        self.key_params = key_params if key_params is not None else None
        self.prefix = prefix
        self.user_id_param = user_id_param

    @property
    def cache_manager(self):
        config = CacheConfig(storage_type=self.storage_type, prefix=self.prefix)
        return UniversalCacheManager(config)

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
            prefix: str = "l_cache:",
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
    await default_cache_registry.preload_all()


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
        prefix: str = "l_cache:",
        storage_type: StorageType = StorageType.REDIS
):
    """失效指定用户的指定缓存键"""
    await l_user_cache.invalidate_cache(user_id, cache_key_enum, key_params, prefix, storage_type)
