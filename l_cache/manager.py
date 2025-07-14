import asyncio
import json
import time
from typing import Any, Optional, Dict, Union

from .config import CacheConfig
from .enums import StorageType, CacheType
from .storages import CacheStorage, MemoryCacheStorage, RedisCacheStorage

from .utils import strify
from loguru import logger

class UniversalCacheManager:
    """
    通用缓存管理器，提供统一的缓存接口。
    
    支持内存和Redis两种存储后端，支持TTL和LRU两种缓存策略。
    提供同步和异步API，支持用户级别版本控制。
    支持全局缓存开关，可以一键关闭所有缓存功能。
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self._storage: CacheStorage = self._create_storage()
        self._global_version = 0
        self._user_versions: Dict[str, int] = {}

    def _create_storage(self) -> CacheStorage:
        """创建存储实例"""
        if self.config.storage_type == StorageType.MEMORY:
            return MemoryCacheStorage(self.config)
        elif self.config.storage_type == StorageType.REDIS:
            return RedisCacheStorage(self.config)
        else:
            raise ValueError(f"Unsupported storage type: {self.config.storage_type}")

    @property
    def is_cache_enabled(self) -> bool:
        """
        检查全局缓存是否已启用
        
        :return: 是否启用
        """
        from .config import is_global_cache_enabled
        return is_global_cache_enabled()

    async def get(self, key: str, user_id: Optional[str] = None) -> Optional[Any]:
        """
        异步获取缓存值
        
        :param key: 缓存键
        :param user_id: 用户ID，用于用户级别版本控制
        :return: 缓存值，如果不存在或已失效则返回None
        """
        if not self.is_cache_enabled:
            return None
            
        try:
            # 构建带版本号的键
            versioned_key = self._build_versioned_key(key, user_id)
            return await self._storage.get(versioned_key)
        except Exception as e:
            logger.error(f"Error getting cache for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, user_id: Optional[str] = None) -> bool:
        """
        异步设置缓存值
        
        :param key: 缓存键
        :param value: 缓存值
        :param ttl_seconds: 过期时间（秒），如果为None则使用配置中的默认值
        :param user_id: 用户ID，用于用户级别版本控制
        :return: 是否设置成功
        """
        if not self.is_cache_enabled:
            return False
            
        try:
            # 构建带版本号的键
            versioned_key = self._build_versioned_key(key, user_id)
            ttl = ttl_seconds or self.config.ttl_seconds
            return await self._storage.set(versioned_key, value, ttl)
        except Exception as e:
            logger.error(f"Error setting cache for key {key}: {e}")
            return False

    async def delete(self, key: str, user_id: Optional[str] = None) -> bool:
        """
        异步删除缓存值
        
        :param key: 缓存键
        :param user_id: 用户ID，用于用户级别版本控制
        :return: 是否删除成功
        """
        if not self.is_cache_enabled:
            return False
            
        try:
            # 构建带版本号的键
            versioned_key = self._build_versioned_key(key, user_id)
            return await self._storage.delete(versioned_key)
        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {e}")
            return False

    def get_sync(self, key: str, user_id: Optional[str] = None) -> Optional[Any]:
        """
        同步获取缓存值（仅支持内存存储）
        
        :param key: 缓存键
        :param user_id: 用户ID，用于用户级别版本控制
        :return: 缓存值，如果不存在或已失效则返回None
        """
        if not self.is_cache_enabled:
            return None
            
        if self.config.storage_type != StorageType.MEMORY:
            raise ValueError("Sync operations are only supported for memory storage")
        
        try:
            versioned_key = self._build_versioned_key(key, user_id)
            return self._storage.get_sync(versioned_key)
        except Exception as e:
            logger.error(f"Error getting cache for key {key}: {e}")
            return None

    def set_sync(self, key: str, value: Any, ttl_seconds: Optional[int] = None, user_id: Optional[str] = None) -> bool:
        """
        同步设置缓存值（仅支持内存存储）
        
        :param key: 缓存键
        :param value: 缓存值
        :param ttl_seconds: 过期时间（秒），如果为None则使用配置中的默认值
        :param user_id: 用户ID，用于用户级别版本控制
        :return: 是否设置成功
        """
        if not self.is_cache_enabled:
            return False
            
        if self.config.storage_type != StorageType.MEMORY:
            raise ValueError("Sync operations are only supported for memory storage")
        
        try:
            versioned_key = self._build_versioned_key(key, user_id)
            ttl = ttl_seconds or self.config.ttl_seconds
            return self._storage.set_sync(versioned_key, value, ttl)
        except Exception as e:
            logger.error(f"Error setting cache for key {key}: {e}")
            return False

    def delete_sync(self, key: str, user_id: Optional[str] = None) -> bool:
        """
        同步删除缓存值（仅支持内存存储）
        
        :param key: 缓存键
        :param user_id: 用户ID，用于用户级别版本控制
        :return: 是否删除成功
        """
        if not self.is_cache_enabled:
            return False
            
        if self.config.storage_type != StorageType.MEMORY:
            raise ValueError("Sync operations are only supported for memory storage")
        
        try:
            # 构建带版本号的键
            versioned_key = self._build_versioned_key(key, user_id)
            return self._storage.delete_sync(versioned_key)
        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {e}")
            return False

    def _build_versioned_key(self, key: str, user_id: Optional[str] = None) -> str:
        """
        构建带版本号的缓存键
        
        :param key: 原始缓存键
        :param user_id: 用户ID
        :return: 带版本号的缓存键
        """
        if user_id:
            # 用户级别版本控制
            user_version = self._user_versions.get(user_id, 0)
            return f"{key}:v{user_version}"
        else:
            # 全局版本控制
            return f"{key}:v{self._global_version}"

    async def increment_global_version(self) -> int:
        """
        递增全局版本号，使所有缓存失效
        
        :return: 新的全局版本号
        """
        self._global_version += 1
        logger.info(f"Global version incremented to {self._global_version}")
        return self._global_version

    async def increment_user_version(self, user_id: str) -> int:
        """
        递增用户版本号，使该用户的所有缓存失效
        
        :param user_id: 用户ID
        :return: 新的用户版本号
        """
        self._user_versions[user_id] = self._user_versions.get(user_id, 0) + 1
        logger.info(f"User {user_id} version incremented to {self._user_versions[user_id]}")
        return self._user_versions[user_id]

    async def invalidate_all(self) -> bool:
        """
        使所有缓存失效
        
        :return: 是否成功
        """
        try:
            await self.increment_global_version()
            return True
        except Exception as e:
            logger.error(f"Error invalidating all caches: {e}")
            return False

    async def invalidate_user_cache(self, user_id: str) -> bool:
        """
        使用户的所有缓存失效
        
        :param user_id: 用户ID
        :return: 是否成功
        """
        try:
            await self.increment_user_version(user_id)
            return True
        except Exception as e:
            logger.error(f"Error invalidating user cache for {user_id}: {e}")
            return False

    @property
    def is_global_cache_enabled_sync(self) -> bool:
        """
        检查内存缓存是否已启用（同步版本）
        
        :return: 是否启用
        """
        if self.config.storage_type != StorageType.MEMORY:
            return False
        return isinstance(self._storage, MemoryCacheStorage) and self._storage.is_enabled

    async def clear(self) -> bool:
        """
        清除所有缓存（异步版本）
        
        :return: 是否成功
        """
        try:
            if self.config.storage_type == StorageType.MEMORY:
                # 对于内存存储，直接清除缓存
                if hasattr(self._storage, 'clear'):
                    await self._storage.clear()
                else:
                    # 如果没有clear方法，通过版本控制来清除
                    await self.increment_global_version()
            else:
                # 对于Redis存储，通过版本控制来清除
                await self.increment_global_version()
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def clear_sync(self) -> bool:
        """
        清除所有缓存（同步版本，仅支持内存存储）
        
        :return: 是否成功
        """
        if self.config.storage_type != StorageType.MEMORY:
            raise ValueError("Sync clear operations are only supported for memory storage")
        
        try:
            if hasattr(self._storage, 'clear_sync'):
                self._storage.clear_sync()
            elif hasattr(self._storage, 'clear'):
                # 如果只有异步clear方法，在同步环境中无法使用
                raise ValueError("Memory storage does not support sync clear operation")
            else:
                # 通过版本控制来清除
                self._global_version += 1
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
