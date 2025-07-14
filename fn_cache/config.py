from typing import Optional, Callable
from pydantic import BaseModel

from .enums import CacheType, StorageType, SerializerType

# 默认缓存前缀常量
DEFAULT_PREFIX = "fn_cache:"

# 全局缓存主开关
GLOBAL_CACHE_SWITCH = True

def enable_global_cache():
    """启用全局缓存功能"""
    global GLOBAL_CACHE_SWITCH
    GLOBAL_CACHE_SWITCH = True

def disable_global_cache():
    """禁用全局缓存功能"""
    global GLOBAL_CACHE_SWITCH
    GLOBAL_CACHE_SWITCH = False

def is_global_cache_enabled():
    """查询全局缓存开关状态"""
    return GLOBAL_CACHE_SWITCH

class CacheConfig(BaseModel):
    """
    缓存配置
    
    :param cache_type: 缓存类型 (LRU/TTL)
    :param storage_type: 存储类型 (REDIS/MEMORY)
    :param ttl_seconds: TTL时间（秒）
    :param max_size: LRU最大容量
    :param prefix: 缓存key前缀
    :param global_version_key: 全局版本号key名称。用于存储一个全局版本号，当缓存项的版本号小于此版本号时，缓存失效。
    :param user_version_key: 用户版本号key名称。用于存储用户级别的版本号，支持按用户失效缓存。
    :param make_expire_sec_func: 动态生成过期时间的函数，接收缓存值作为参数，返回过期秒数
    :param serializer_type: 序列化器类型 (JSON/PICKLE/MESSAGEPACK/STRING)
    :param serializer_kwargs: 序列化器参数
    :param enable_statistics: 是否启用缓存统计
    :param enable_memory_monitoring: 是否启用内存监控
    :param redis_config: Redis连接配置
    """
    cache_type: CacheType = CacheType.TTL
    storage_type: StorageType = StorageType.MEMORY
    ttl_seconds: int = 600
    max_size: int = 1000
    prefix: str = DEFAULT_PREFIX
    global_version_key: str = f"{DEFAULT_PREFIX}global:version"
    user_version_key: str = f"{DEFAULT_PREFIX}user:version:{{user_id}}"
    make_expire_sec_func: Optional[Callable] = None
    serializer_type: SerializerType = SerializerType.JSON
    serializer_kwargs: dict = {}
    enable_statistics: bool = True
    enable_memory_monitoring: bool = True
    redis_config: dict = {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "decode_responses": True,
        "socket_timeout": 1.0,
        "socket_connect_timeout": 1.0,
        "retry_on_timeout": True,
        "health_check_interval": 30,
    }
