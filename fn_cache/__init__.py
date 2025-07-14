"""
L-Cache: 轻量级通用缓存库

这是一个支持多种存储后端（内存、Redis）和缓存策略（LRU、TTL）的通用缓存库。
提供同步和异步API，支持函数装饰器和直接调用方式，参考 aiocache 的设计模式。

主要特性：
- 支持内存和Redis两种存储后端
- 支持LRU和TTL两种缓存策略
- 提供同步和异步API
- 支持函数装饰器
- 支持一键失效所有缓存
- 支持自定义缓存key生成策略
- 支持动态过期时间计算
- 支持缓存预加载功能
- 支持内存占用监控和定期报告
- 支持多种序列化格式（JSON、Pickle、MessagePack）
- 支持缓存统计和性能监控
- 支持缓存预热和批量操作

基本用法:
    
    # 使用通用装饰器
    @cached(ttl_seconds=300)
    def my_function(arg1, arg2):
        return expensive_computation(arg1, arg2)
    
    # 使用自定义缓存键生成器
    def custom_key_func(*args, **kwargs):
        return f"custom:{args[0]}:{kwargs.get('param2', 'default')}"
    
    @cached(key_func=custom_key_func, ttl_seconds=300)
    async def get_user_info(user_id: int, param2="default"):
        return await fetch_user_info(user_id)
    
    # 直接使用缓存管理器
    cache_manager = UniversalCacheManager()
    await cache_manager.set("key", "value", ttl_seconds=300)
    value = await cache_manager.get("key")
    
    # 通过装饰后的函数访问缓存管理器
    cached_func = cached(ttl_seconds=300)(my_function)
    cached_func.cache.clear()  # 清除该函数的缓存
    
    # 内存监控功能
    start_cache_memory_monitoring(interval_seconds=300)  # 每5分钟监控一次
    memory_usage = get_cache_memory_usage()  # 获取内存使用情况
    summary = get_cache_memory_summary()  # 获取内存使用摘要
    
    # 缓存统计
    stats = get_cache_statistics()  # 获取缓存统计信息
"""

from .config import CacheConfig, enable_global_cache, disable_global_cache, is_global_cache_enabled
from .decorators import (
    invalidate_all_caches,
    cached,
    preload_all_caches,
    # 内存监控相关
    start_cache_memory_monitoring,
    stop_cache_memory_monitoring,
    get_cache_memory_usage,
    get_cache_memory_summary,
    register_cache_manager_for_monitoring,
    unregister_cache_manager_from_monitoring,
    MemoryUsageInfo,
    # 缓存统计相关
    get_cache_statistics,
    reset_cache_statistics,
    CacheStatistics,
)
from .enums import CacheKeyEnum, CacheType, StorageType, SerializerType
from .manager import UniversalCacheManager
from .storages import CacheStorage, MemoryCacheStorage, RedisCacheStorage
from .utils import safe_redis_operation, safe_redis_void_operation
from .utils.serializers import Serializer, JsonSerializer, PickleSerializer, MessagePackSerializer

__all__ = [
    # 管理器和存储
    "UniversalCacheManager",
    "CacheStorage",
    "RedisCacheStorage",
    "MemoryCacheStorage",

    # 配置和枚举
    "CacheConfig",
    "enable_global_cache",
    "disable_global_cache",
    "is_global_cache_enabled",
    "CacheKeyEnum",
    "CacheType",
    "StorageType",
    "SerializerType",

    # 装饰器
    "cached",

    # 工具函数
    "invalidate_all_caches",
    "preload_all_caches",

    # redis操作工具
    "safe_redis_operation",
    "safe_redis_void_operation",
    
    # 内存监控相关
    "start_cache_memory_monitoring",
    "stop_cache_memory_monitoring",
    "get_cache_memory_usage",
    "get_cache_memory_summary",
    "register_cache_manager_for_monitoring",
    "unregister_cache_manager_from_monitoring",
    "MemoryUsageInfo",
    
    # 缓存统计相关
    "get_cache_statistics",
    "reset_cache_statistics",
    "CacheStatistics",
    
    # 序列化器
    "Serializer",
    "JsonSerializer",
    "PickleSerializer",
    "MessagePackSerializer",
]

__version__ = "0.1.2"
__author__ = "WangZhanze <leolswq@163.com>"
__description__ = "轻量级通用缓存库"
