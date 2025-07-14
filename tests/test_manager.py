"""
缓存管理器测试
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from fn_cache import UniversalCacheManager, CacheConfig, CacheType, StorageType
from fn_cache.storages import MemoryCacheStorage


class TestUniversalCacheManager:
    """通用缓存管理器测试类"""

    def test_init_with_default_config(self):
        """测试使用默认配置初始化"""
        manager = UniversalCacheManager()
        assert manager.config.storage_type == StorageType.MEMORY
        assert manager.config.cache_type == CacheType.TTL
        assert manager.config.ttl_seconds == 600
        assert manager.config.max_size == 1000
        assert manager._global_version == 0
        assert manager._user_versions == {}

    def test_init_with_custom_config(self):
        """测试使用自定义配置初始化"""
        config = CacheConfig(
            storage_type=StorageType.REDIS,
            cache_type=CacheType.LRU,
            ttl_seconds=300,
            max_size=500,
            prefix="custom:"
        )
        manager = UniversalCacheManager(config)
        assert manager.config == config

    def test_create_storage_memory(self):
        """测试创建内存存储"""
        config = CacheConfig(storage_type=StorageType.MEMORY)
        manager = UniversalCacheManager(config)
        assert isinstance(manager._storage, MemoryCacheStorage)


    def test_create_storage_invalid_type(self):
        """测试创建无效存储类型"""
        with pytest.raises(ValueError, match="Input should be 'redis' or 'memory'"):
            config = CacheConfig(storage_type="INVALID")

    def test_build_versioned_key_global(self):
        """测试构建全局版本键"""
        manager = UniversalCacheManager()
        key = manager._build_versioned_key("test_key")
        assert key == "test_key:v0"

    def test_build_versioned_key_user(self):
        """测试构建用户版本键"""
        manager = UniversalCacheManager()
        key = manager._build_versioned_key("test_key", user_id="123")
        assert key == "test_key:v0"

    def test_build_versioned_key_user_with_version(self):
        """测试构建带版本的用户键"""
        manager = UniversalCacheManager()
        manager._user_versions["123"] = 5
        key = manager._build_versioned_key("test_key", user_id="123")
        assert key == "test_key:v5"

    @pytest.mark.asyncio
    async def test_get_success(self):
        """测试成功获取缓存"""
        manager = UniversalCacheManager()
        await manager.set("test_key", "test_value", ttl_seconds=60)
        value = await manager.get("test_key")
        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        """测试获取不存在的缓存"""
        manager = UniversalCacheManager()
        value = await manager.get("nonexistent_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_get_with_storage_error(self):
        """测试存储错误时的获取"""
        manager = UniversalCacheManager()
        # 模拟存储错误
        manager._storage.get = AsyncMock(side_effect=Exception("Storage error"))
        value = await manager.get("test_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_set_success(self):
        """测试成功设置缓存"""
        manager = UniversalCacheManager()
        result = await manager.set("test_key", "test_value", ttl_seconds=60)
        assert result is True
        value = await manager.get("test_key")
        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self):
        """测试使用自定义TTL设置缓存"""
        manager = UniversalCacheManager()
        result = await manager.set("test_key", "test_value", ttl_seconds=120)
        assert result is True

    @pytest.mark.asyncio
    async def test_set_with_storage_error(self):
        """测试存储错误时的设置"""
        manager = UniversalCacheManager()
        # 模拟存储错误
        manager._storage.set = AsyncMock(side_effect=Exception("Storage error"))
        result = await manager.set("test_key", "test_value", ttl_seconds=60)
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_success(self):
        """测试成功删除缓存"""
        manager = UniversalCacheManager()
        await manager.set("test_key", "test_value", ttl_seconds=60)
        result = await manager.delete("test_key")
        assert result is True
        value = await manager.get("test_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        """测试删除不存在的缓存"""
        manager = UniversalCacheManager()
        result = await manager.delete("nonexistent_key")
        assert result is True  # 删除不存在的键通常返回True

    @pytest.mark.asyncio
    async def test_delete_with_storage_error(self):
        """测试存储错误时的删除"""
        manager = UniversalCacheManager()
        # 模拟存储错误
        manager._storage.delete = AsyncMock(side_effect=Exception("Storage error"))
        result = await manager.delete("test_key")
        assert result is False

    def test_get_sync_memory_storage(self):
        """测试内存存储的同步获取"""
        manager = UniversalCacheManager()
        manager.set_sync("test_key", "test_value", ttl_seconds=60)
        value = manager.get_sync("test_key")
        assert value == "test_value"



    def test_set_sync_memory_storage(self):
        """测试内存存储的同步设置"""
        manager = UniversalCacheManager()
        result = manager.set_sync("test_key", "test_value", ttl_seconds=60)
        assert result is True
        value = manager.get_sync("test_key")
        assert value == "test_value"



    def test_delete_sync_memory_storage(self):
        """测试内存存储的同步删除"""
        manager = UniversalCacheManager()
        manager.set_sync("test_key", "test_value", ttl_seconds=60)
        result = manager.delete_sync("test_key")
        assert result is True
        value = manager.get_sync("test_key")
        assert value is None



    @pytest.mark.asyncio
    async def test_increment_global_version(self):
        """测试递增全局版本"""
        manager = UniversalCacheManager()
        initial_version = manager._global_version
        
        new_version = await manager.increment_global_version()
        assert new_version == initial_version + 1
        assert manager._global_version == new_version

    @pytest.mark.asyncio
    async def test_increment_user_version(self):
        """测试递增用户版本"""
        manager = UniversalCacheManager()
        user_id = "123"
        
        # 第一次递增
        new_version = await manager.increment_user_version(user_id)
        assert new_version == 1
        assert manager._user_versions[user_id] == 1
        
        # 第二次递增
        new_version = await manager.increment_user_version(user_id)
        assert new_version == 2
        assert manager._user_versions[user_id] == 2

    @pytest.mark.asyncio
    async def test_increment_user_version_multiple_users(self):
        """测试多个用户的版本递增"""
        manager = UniversalCacheManager()
        
        # 递增用户1的版本
        version1 = await manager.increment_user_version("user1")
        assert version1 == 1
        
        # 递增用户2的版本
        version2 = await manager.increment_user_version("user2")
        assert version2 == 1
        
        # 再次递增用户1的版本
        version1_2 = await manager.increment_user_version("user1")
        assert version1_2 == 2
        
        assert manager._user_versions["user1"] == 2
        assert manager._user_versions["user2"] == 1

    @pytest.mark.asyncio
    async def test_invalidate_all_success(self):
        """测试成功使所有缓存失效"""
        manager = UniversalCacheManager()
        result = await manager.invalidate_all()
        assert result is True
        assert manager._global_version == 1

    @pytest.mark.asyncio
    async def test_invalidate_all_with_error(self):
        """测试使所有缓存失效时出错"""
        manager = UniversalCacheManager()
        # 模拟递增版本时出错
        manager.increment_global_version = AsyncMock(side_effect=Exception("Version error"))
        result = await manager.invalidate_all()
        assert result is False

    @pytest.mark.asyncio
    async def test_invalidate_user_cache_success(self):
        """测试成功使用户缓存失效"""
        manager = UniversalCacheManager()
        user_id = "123"
        result = await manager.invalidate_user_cache(user_id)
        assert result is True
        assert manager._user_versions[user_id] == 1

    @pytest.mark.asyncio
    async def test_invalidate_user_cache_with_error(self):
        """测试使用户缓存失效时出错"""
        manager = UniversalCacheManager()
        # 模拟递增版本时出错
        manager.increment_user_version = AsyncMock(side_effect=Exception("Version error"))
        result = await manager.invalidate_user_cache("123")
        assert result is False

    @pytest.mark.asyncio
    async def test_version_control_global_cache(self):
        """测试全局版本控制"""
        manager = UniversalCacheManager()
        
        # 设置缓存
        await manager.set("key1", "value1", ttl_seconds=60)
        await manager.set("key2", "value2", ttl_seconds=60)
        
        # 验证缓存存在
        assert await manager.get("key1") == "value1"
        assert await manager.get("key2") == "value2"
        
        # 递增全局版本
        await manager.increment_global_version()
        
        # 验证缓存已失效
        assert await manager.get("key1") is None
        assert await manager.get("key2") is None

    @pytest.mark.asyncio
    async def test_version_controcached(self):
        """测试用户版本控制"""
        manager = UniversalCacheManager()
        
        # 设置用户缓存和全局缓存
        await manager.set("user_key", "user_value", ttl_seconds=60, user_id="123")
        await manager.set("global_key", "global_value", ttl_seconds=60)
        
        # 验证缓存存在
        assert await manager.get("user_key", user_id="123") == "user_value"
        assert await manager.get("global_key") == "global_value"
        
        # 递增用户版本
        await manager.increment_user_version("123")
        
        # 验证用户缓存已失效，全局缓存仍然存在
        assert await manager.get("user_key", user_id="123") is None
        assert await manager.get("global_key") == "global_value"

    @pytest.mark.asyncio
    async def test_version_control_multiple_users(self):
        """测试多用户版本控制"""
        manager = UniversalCacheManager()
        
        # 为不同用户设置缓存
        await manager.set("key1", "value1", ttl_seconds=60, user_id="user1")
        await manager.set("key2", "value2", ttl_seconds=60, user_id="user2")
        
        # 验证缓存存在
        assert await manager.get("key1", user_id="user1") == "value1"
        assert await manager.get("key2", user_id="user2") == "value2"
        
        # 只递增用户1的版本
        await manager.increment_user_version("user1")
        
        # 验证用户1的缓存已失效，用户2的缓存仍然存在
        assert await manager.get("key1", user_id="user1") is None
        assert await manager.get("key2", user_id="user2") == "value2"

    @pytest.mark.asyncio
    async def test_complex_data_types(self):
        """测试复杂数据类型"""
        manager = UniversalCacheManager()
        
        # 测试字典
        test_dict = {"key": "value", "number": 123, "list": [1, 2, 3]}
        await manager.set("dict_key", test_dict, ttl_seconds=60)
        retrieved_dict = await manager.get("dict_key")
        assert retrieved_dict == test_dict
        
        # 测试列表
        test_list = [1, "string", {"nested": "value"}]
        await manager.set("list_key", test_list, ttl_seconds=60)
        retrieved_list = await manager.get("list_key")
        assert retrieved_list == test_list
        
        # 测试None值
        await manager.set("none_key", None, ttl_seconds=60)
        retrieved_none = await manager.get("none_key")
        assert retrieved_none is None

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """测试并发操作"""
        manager = UniversalCacheManager()
        
        async def set_cache(key, value):
            await manager.set(key, value, ttl_seconds=60)
            return await manager.get(key)
        
        # 并发设置多个缓存
        tasks = [
            set_cache(f"key_{i}", f"value_{i}")
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 验证所有缓存都设置成功
        for i, result in enumerate(results):
            assert result == f"value_{i}"

    @pytest.mark.asyncio
    async def test_concurrent_version_increments(self):
        """测试并发版本递增"""
        manager = UniversalCacheManager()
        
        async def increment_global():
            return await manager.increment_global_version()
        
        async def increment_user(user_id):
            return await manager.increment_user_version(user_id)
        
        # 并发递增版本
        tasks = [
            increment_global(),
            increment_user("user1"),
            increment_user("user2"),
            increment_global(),
            increment_user("user1")
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 验证版本递增成功
        assert manager._global_version >= 2
        assert manager._user_versions["user1"] >= 2
        assert manager._user_versions["user2"] >= 1 