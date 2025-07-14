from enum import Enum


class CacheType(str, Enum):
    """缓存类型枚举"""
    LRU = "lru"  # 最近最少使用
    TTL = "ttl"  # 基于时间过期


class StorageType(str, Enum):
    """存储类型枚举"""
    REDIS = "redis"
    MEMORY = "memory"


class SerializerType(str, Enum):
    """序列化类型枚举"""
    JSON = "json"  # JSON序列化（默认）
    PICKLE = "pickle"  # Pickle序列化
    MESSAGEPACK = "msgpack"  # MessagePack序列化
    STRING = "string"  # 字符串序列化


class CacheKeyEnum(str, Enum):
    """
    缓存键枚举基类
    
    用于定义特定业务场景的缓存键模板，支持参数化替换。
    """
    USER_AVAILABLE_CHARACTER_IDs = "user:{user_id}:available_character_ids"
    USER_AVAILABLE_FIGURE_IDs = "user:{user_id}:available_figure_ids"

    def format(self, **kwargs) -> str:
        """
        格式化缓存键，替换模板中的参数
        
        Args:
            **kwargs: 要替换的参数
            
        Returns:
            格式化后的缓存键
        """
        return self.value.format(**kwargs)
