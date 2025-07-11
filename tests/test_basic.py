"""
基本功能测试
"""

import pytest
import asyncio
from enum import Enum
from unittest.mock import AsyncMock, MagicMock

from l_cache import (
    UniversalCacheManager,
    CacheConfig,
    CacheType,
    StorageType,
    u_l_cache,
    l_user_cache,
    CacheKeyEnum,
)
from l_cache.storages import MemoryCacheStorage


class TestCacheKeyEnum(str, Enum):
    """测试用缓存键枚举"""
    TEST_KEY = "test:key:{param}"
    USER_KEY = "user:data:{user_id}"
    
    def format(self, **kwargs) -> str:
        """格式化缓存键，替换模板中的参数"""
        return self.value.format(**kwargs)


class TestBasicFunctionality:
    """基本功能测试类"""
    
    def test_cache_config(self):
        """测试缓存配置"""
        config = CacheConfig(
            cache_type=CacheType.TTL,
            storage_type=StorageType.MEMORY,
            ttl_seconds=300,
            max_size=1000,
            prefix="test:"
        )
        
        assert config.cache_type == CacheType.TTL
        assert config.storage_type == StorageType.MEMORY
        assert config.ttl_seconds == 300
        assert config.max_size == 1000
        assert config.prefix == "test:"
    
    def test_cache_key_enum(self):
        """测试缓存键枚举"""
        key = TestCacheKeyEnum.TEST_KEY.format(param="value")
        assert key == "test:key:value"
        
        user_key = TestCacheKeyEnum.USER_KEY.format(user_id=123)
        assert user_key == "user:data:123"
    
    def test_memory_storage(self):
        """测试内存存储"""
        storage = MemoryCacheStorage(CacheConfig())
        
        # 测试同步操作
        storage.set_sync("test_key", "test_value", ttl_seconds=60)
        value = storage.get_sync("test_key")
        assert value == "test_value"
        
        # 测试删除
        storage.delete_sync("test_key")
        value = storage.get_sync("test_key")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_async_memory_storage(self):
        """测试异步内存存储"""
        storage = MemoryCacheStorage(CacheConfig())
        
        # 测试异步操作
        await storage.set("test_key", "test_value", ttl_seconds=60)
        value = await storage.get("test_key")
        assert value == "test_value"
        
        # 测试删除
        await storage.delete("test_key")
        value = await storage.get("test_key")
        assert value is None
    
    def test_universal_cache_manager_sync(self):
        """测试通用缓存管理器同步操作"""
        manager = UniversalCacheManager(CacheConfig())
        
        # 测试同步操作
        manager.set_sync("test_key", "test_value", ttl_seconds=60)
        value = manager.get_sync("test_key")
        assert value == "test_value"
        
        # 测试删除
        manager.delete_sync("test_key")
        value = manager.get_sync("test_key")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_universal_cache_manager_async(self):
        """测试通用缓存管理器异步操作"""
        manager = UniversalCacheManager(CacheConfig())
        
        # 测试异步操作
        await manager.set("test_key", "test_value", ttl_seconds=60)
        value = await manager.get("test_key")
        assert value == "test_value"
        
        # 测试删除
        await manager.delete("test_key")
        value = await manager.get("test_key")
        assert value is None
    
    def test_u_l_cache_decorator_sync(self):
        """测试 u_l_cache 装饰器同步函数"""
        call_count = 0
        
        @u_l_cache(ttl_seconds=60)
        def test_function(param):
            nonlocal call_count
            call_count += 1
            return f"result_{param}"
        
        # 第一次调用
        result1 = test_function("test")
        assert result1 == "result_test"
        assert call_count == 1
        
        # 第二次调用（应该从缓存返回）
        result2 = test_function("test")
        assert result2 == "result_test"
        assert call_count == 1  # 调用次数不应该增加
    
    @pytest.mark.asyncio
    async def test_u_l_cache_decorator_async(self):
        """测试 u_l_cache 装饰器异步函数"""
        call_count = 0
        
        @u_l_cache(ttl_seconds=60)
        async def test_async_function(param):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # 模拟异步操作
            return f"async_result_{param}"
        
        # 第一次调用
        result1 = await test_async_function("test")
        assert result1 == "async_result_test"
        assert call_count == 1
        
        # 第二次调用（应该从缓存返回）
        result2 = await test_async_function("test")
        assert result2 == "async_result_test"
        assert call_count == 1  # 调用次数不应该增加
    
    def test_l_user_cache_decorator(self):
        """测试 l_user_cache 装饰器"""
        call_count = 0
        
        @l_user_cache(
            cache_key=TestCacheKeyEnum.USER_KEY,
            key_params=["user_id"],
            storage_type=StorageType.MEMORY
        )
        def get_user_data(user_id: int):
            nonlocal call_count
            call_count += 1
            return {"user_id": user_id, "data": "user_data"}
        
        # 第一次调用
        result1 = get_user_data(123)
        assert result1["user_id"] == 123
        assert call_count == 1
        
        # 第二次调用（应该从缓存返回）
        result2 = get_user_data(123)
        assert result2["user_id"] == 123
        assert call_count == 1  # 调用次数不应该增加
        
        # 不同用户ID应该重新调用
        result3 = get_user_data(456)
        assert result3["user_id"] == 456
        assert call_count == 2  # 调用次数应该增加



class TestCacheInvalidation:
    """缓存失效测试类"""
    
    @pytest.mark.asyncio
    async def test_global_version_invalidation(self):
        """测试全局版本失效"""
        manager = UniversalCacheManager(CacheConfig())
        
        # 设置一些缓存
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
    async def test_user_version_invalidation(self):
        """测试用户版本失效"""
        manager = UniversalCacheManager(CacheConfig())
        
        # 为用户设置缓存
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


if __name__ == "__main__":
    pytest.main([__file__]) 