import asyncio
import json
import time
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from collections import OrderedDict

from .config import CacheConfig
from .enums import CacheType, StorageType
from loguru import logger

class CacheStorage(ABC):
    """缓存存储抽象基类"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """异步获取缓存值"""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """异步设置缓存值"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """异步删除缓存值"""
        pass

    @abstractmethod
    def get_sync(self, key: str) -> Optional[Any]:
        """同步获取缓存值"""
        pass

    @abstractmethod
    def set_sync(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """同步设置缓存值"""
        pass

    @abstractmethod
    def delete_sync(self, key: str) -> bool:
        """同步删除缓存值"""
        pass


class MemoryCacheStorage(CacheStorage):
    """内存缓存存储实现"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.is_enabled = True
        
        if config.cache_type == CacheType.TTL:
            self._cache: Dict[str, tuple[Any, float]] = {}
        else:  # LRU
            self._cache = OrderedDict()
            self._max_size = config.max_size

    async def get(self, key: str) -> Optional[Any]:
        """异步获取缓存值"""
        return self.get_sync(key)

    async def set(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """异步设置缓存值"""
        return self.set_sync(key, value, ttl_seconds)

    async def delete(self, key: str) -> bool:
        """异步删除缓存值"""
        return self.delete_sync(key)

    def get_sync(self, key: str) -> Optional[Any]:
        """同步获取缓存值"""
        if not self.is_enabled:
            return None

        if self.config.cache_type == CacheType.TTL:
            return self._get_ttl(key)
        else:  # LRU
            return self._get_lru(key)

    def set_sync(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """同步设置缓存值"""
        if not self.is_enabled:
            return False

        try:
            if self.config.cache_type == CacheType.TTL:
                return self._set_ttl(key, value, ttl_seconds)
            else:  # LRU
                return self._set_lru(key, value)
        except Exception:
            return False

    def delete_sync(self, key: str) -> bool:
        """同步删除缓存值"""
        if not self.is_enabled:
            return False

        try:
            if key in self._cache:
                del self._cache[key]
            return True  # 删除操作总是成功，无论键是否存在
        except Exception:
            return False

    def _get_ttl(self, key: str) -> Optional[Any]:
        """TTL缓存获取"""
        if key not in self._cache:
            return None

        value, expire_time = self._cache[key]
        if time.time() > expire_time:
            # 过期，删除并返回None
            del self._cache[key]
            return None

        return value

    def _set_ttl(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """TTL缓存设置"""
        try:
            expire_time = time.time() + ttl_seconds
            self._cache[key] = (value, expire_time)
            return True
        except Exception:
            return False

    def _get_lru(self, key: str) -> Optional[Any]:
        """LRU缓存获取"""
        if key not in self._cache:
            return None

        # 移动到末尾（最近使用）
        value = self._cache.pop(key)
        self._cache[key] = value
        return value

    def _set_lru(self, key: str, value: Any) -> bool:
        """LRU缓存设置"""
        try:
            if key in self._cache:
                # 已存在，移动到末尾
                self._cache.pop(key)
            elif len(self._cache) >= self._max_size:
                # 缓存已满，删除最久未使用的项
                self._cache.popitem(last=False)

            self._cache[key] = value
            return True
        except Exception:
            return False


class RedisCacheStorage(CacheStorage):
    """Redis缓存存储实现"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self._redis = None
        self._prefix = config.prefix

    async def _get_redis(self):
        """获取Redis连接"""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = redis.Redis(
                    host='localhost',
                    port=6379,
                    db=0,
                    decode_responses=True,
                    socket_timeout=1.0,
                    socket_connect_timeout=1.0
                )
            except ImportError:
                raise ImportError("Redis is required for RedisCacheStorage. Install with: pip install redis")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        return self._redis

    async def get(self, key: str) -> Optional[Any]:
        """异步获取缓存值"""
        try:
            redis_client = await self._get_redis()
            full_key = f"{self._prefix}{key}"
            value = await redis_client.get(full_key)
            
            if value is None:
                return None

            # 尝试解析JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """异步设置缓存值"""
        try:
            redis_client = await self._get_redis()
            full_key = f"{self._prefix}{key}"
            
            # 序列化值
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value, ensure_ascii=False)
            else:
                serialized_value = str(value)

            await redis_client.setex(full_key, ttl_seconds, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """异步删除缓存值"""
        try:
            redis_client = await self._get_redis()
            full_key = f"{self._prefix}{key}"
            await redis_client.delete(full_key)
            return True  # 删除操作总是成功，无论键是否存在
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False

    def get_sync(self, key: str) -> Optional[Any]:
        """同步获取缓存值（Redis不支持同步操作）"""
        raise NotImplementedError("Redis storage does not support sync operations")

    def set_sync(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """同步设置缓存值（Redis不支持同步操作）"""
        raise NotImplementedError("Redis storage does not support sync operations")

    def delete_sync(self, key: str) -> bool:
        """同步删除缓存值（Redis不支持同步操作）"""
        raise NotImplementedError("Redis storage does not support sync operations") 