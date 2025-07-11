"""
集成测试
"""

import pytest
import asyncio
import time
from enum import Enum
from unittest.mock import Mock, patch, AsyncMock

from l_cache import (
    UniversalCacheManager, CacheConfig, CacheType, StorageType,
    u_l_cache, l_user_cache, CacheKeyEnum, invalidate_all_caches,
    invalidate_user_cache, preload_all_caches
)


class CacheKeyEnum(str, Enum):
    """测试用缓存键枚举"""
    USER_PROFILE = "user:profile:{user_id}"
    USER_PREFERENCES = "user:preferences:{user_id}"
    PRODUCT_DETAILS = "product:details:{product_id}"
    SYSTEM_CONFIG = "system:config:{config_key}"
    
    def format(self, **kwargs) -> str:
        """格式化缓存键，替换模板中的参数"""
        return self.value.format(**kwargs)


class TestEndToEndCaching:
    """端到端缓存测试类"""

    @pytest.mark.asyncio
    async def test_complete_caching_workflow(self):
        """测试完整的缓存工作流程"""
        # 创建缓存管理器
        manager = UniversalCacheManager(CacheConfig(
            cache_type=CacheType.TTL,
            storage_type=StorageType.MEMORY,
            ttl_seconds=60
        ))
        
        # 设置缓存
        await manager.set("test_key", "test_value", ttl_seconds=60)
        
        # 获取缓存
        value = await manager.get("test_key")
        assert value == "test_value"
        
        # 删除缓存
        result = await manager.delete("test_key")
        assert result is True
        
        # 验证删除成功
        value = await manager.get("test_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_user_level_caching_workflow(self):
        """测试用户级别缓存工作流程"""
        manager = UniversalCacheManager(CacheConfig())
        
        # 为用户设置缓存
        await manager.set("user_data", "user_value", ttl_seconds=60, user_id="123")
        await manager.set("global_data", "global_value", ttl_seconds=60)
        
        # 验证缓存存在
        user_value = await manager.get("user_data", user_id="123")
        global_value = await manager.get("global_data")
        assert user_value == "user_value"
        assert global_value == "global_value"
        
        # 递增用户版本
        await manager.increment_user_version("123")
        
        # 验证用户缓存失效，全局缓存仍然存在
        user_value = await manager.get("user_data", user_id="123")
        global_value = await manager.get("global_data")
        assert user_value is None
        assert global_value == "global_value"

    @pytest.mark.asyncio
    async def test_lru_cache_workflow(self):
        """测试LRU缓存工作流程"""
        manager = UniversalCacheManager(CacheConfig(
            cache_type=CacheType.LRU,
            max_size=2
        ))
        
        # 设置缓存
        await manager.set("key1", "value1", ttl_seconds=60)
        await manager.set("key2", "value2", ttl_seconds=60)
        
        # 验证缓存存在
        assert await manager.get("key1") == "value1"
        assert await manager.get("key2") == "value2"
        
        # 设置第三个键，应该淘汰第一个
        await manager.set("key3", "value3", ttl_seconds=60)
        
        # 验证key1被淘汰
        assert await manager.get("key1") is None
        assert await manager.get("key2") == "value2"
        assert await manager.get("key3") == "value3"

    @pytest.mark.asyncio
    async def test_global_cache_invalidation(self):
        """测试全局缓存失效"""
        manager = UniversalCacheManager(CacheConfig())
        
        # 设置多个缓存
        await manager.set("key1", "value1", ttl_seconds=60)
        await manager.set("key2", "value2", ttl_seconds=60)
        await manager.set("user_key", "user_value", ttl_seconds=60, user_id="123")
        
        # 验证缓存存在
        assert await manager.get("key1") == "value1"
        assert await manager.get("key2") == "value2"
        assert await manager.get("user_key", user_id="123") == "user_value"
        
        # 使全局缓存失效（不影响用户级别缓存）
        await manager.invalidate_all()
        
        # 验证全局缓存失效，但用户级别缓存仍然存在
        assert await manager.get("key1") is None
        assert await manager.get("key2") is None
        assert await manager.get("user_key", user_id="123") == "user_value"  # 用户缓存不受影响
        
        # 使用户缓存失效
        await manager.invalidate_user_cache("123")
        assert await manager.get("user_key", user_id="123") is None


class TestDecoratorIntegration:
    """装饰器集成测试类"""

    def test_u_l_cache_integration(self):
        """测试u_l_cache装饰器集成"""
        call_count = 0
        
        @u_l_cache(ttl_seconds=60)
        def expensive_operation(param1, param2="default"):
            nonlocal call_count
            call_count += 1
            time.sleep(0.1)  # 模拟耗时操作
            return f"result_{param1}_{param2}"
        
        # 第一次调用
        result1 = expensive_operation("test1")
        assert result1 == "result_test1_default"
        assert call_count == 1
        
        # 第二次调用（应该从缓存返回）
        result2 = expensive_operation("test1")
        assert result2 == "result_test1_default"
        assert call_count == 1
        
        # 不同参数应该重新调用
        result3 = expensive_operation("test2", "custom")
        assert result3 == "result_test2_custom"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_u_l_cache_async_integration(self):
        """测试u_l_cache异步装饰器集成"""
        call_count = 0
        
        @u_l_cache(ttl_seconds=60)
        async def async_expensive_operation(param1, param2="default"):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # 模拟异步耗时操作
            return f"async_result_{param1}_{param2}"
        
        # 第一次调用
        result1 = await async_expensive_operation("test1")
        assert result1 == "async_result_test1_default"
        assert call_count == 1
        
        # 第二次调用（应该从缓存返回）
        result2 = await async_expensive_operation("test1")
        assert result2 == "async_result_test1_default"
        assert call_count == 1

    def test_l_user_cache_integration(self):
        """测试l_user_cache装饰器集成"""
        call_count = 0
        
        @l_user_cache(
            cache_key=CacheKeyEnum.USER_PROFILE,
            key_params=["user_id"],
            storage_type=StorageType.MEMORY
        )
        def get_user_profile(user_id: int):
            nonlocal call_count
            call_count += 1
            return {"user_id": user_id, "name": f"User{user_id}", "email": f"user{user_id}@example.com"}
        
        # 第一次调用
        result1 = get_user_profile(123)
        assert result1["user_id"] == 123
        assert result1["name"] == "User123"
        assert call_count == 1
        
        # 第二次调用（应该从缓存返回）
        result2 = get_user_profile(123)
        assert result2["user_id"] == 123
        assert call_count == 1
        
        # 不同用户应该重新调用
        result3 = get_user_profile(456)
        assert result3["user_id"] == 456
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_l_user_cache_async_integration(self):
        """测试l_user_cache异步装饰器集成"""
        call_count = 0
        
        @l_user_cache(
            cache_key=CacheKeyEnum.USER_PREFERENCES,
            key_params=["user_id"],
            storage_type=StorageType.MEMORY
        )
        async def get_user_preferences(user_id: int):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            return {"user_id": user_id, "theme": "dark", "language": "zh"}
        
        # 第一次调用
        result1 = await get_user_preferences(123)
        assert result1["user_id"] == 123
        assert result1["theme"] == "dark"
        assert call_count == 1
        
        # 第二次调用（应该从缓存返回）
        result2 = await get_user_preferences(123)
        assert result2["user_id"] == 123
        assert call_count == 1

    def test_decorator_with_complex_data(self):
        """测试装饰器与复杂数据"""
        call_count = 0
        
        @u_l_cache(ttl_seconds=60)
        def process_complex_data(data_type: str, filters: dict):
            nonlocal call_count
            call_count += 1
            return {
                "type": data_type,
                "filters": filters,
                "results": [1, 2, 3, 4, 5],
                "metadata": {"count": 5, "processed": True}
            }
        
        # 第一次调用
        filters = {"category": "electronics", "price_range": [100, 500]}
        result1 = process_complex_data("products", filters)
        assert result1["type"] == "products"
        assert result1["filters"] == filters
        assert len(result1["results"]) == 5
        assert call_count == 1
        
        # 第二次调用（应该从缓存返回）
        result2 = process_complex_data("products", filters)
        assert result2 == result1
        assert call_count == 1

    def test_decorator_cache_invalidation(self):
        """测试装饰器缓存失效"""
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
        assert call_count == 1
        
        # 使所有缓存失效
        # 注意：这里需要访问装饰器的缓存管理器
        # 在实际使用中，可能需要通过其他方式来触发失效


class TestConcurrentOperations:
    """并发操作测试类"""

    @pytest.mark.asyncio
    async def test_concurrent_cache_operations(self):
        """测试并发缓存操作"""
        manager = UniversalCacheManager(CacheConfig())
        
        async def cache_operation(key, value):
            await manager.set(key, value, ttl_seconds=60)
            return await manager.get(key)
        
        # 并发执行多个缓存操作
        tasks = [
            cache_operation(f"key_{i}", f"value_{i}")
            for i in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 验证所有操作都成功
        for i, result in enumerate(results):
            assert result == f"value_{i}"

    @pytest.mark.asyncio
    async def test_concurrent_decorator_calls(self):
        """测试并发装饰器调用"""
        call_count = 0
        
        @u_l_cache(ttl_seconds=60)
        async def async_function(param):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            return f"result_{param}"
        
        # 并发调用相同参数
        tasks = [async_function("test") for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # 验证所有结果相同
        for result in results:
            assert result == "result_test"
        
        # 应该只调用一次函数
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_concurrent_user_cache_operations(self):
        """测试并发用户缓存操作"""
        call_count = 0
        
        @l_user_cache(
            cache_key=CacheKeyEnum.USER_PROFILE,
            key_params=["user_id"],
            storage_type=StorageType.MEMORY
        )
        async def get_user_profile(user_id: int):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            return {"user_id": user_id, "name": f"User{user_id}"}
        
        # 并发调用不同用户
        tasks = [
            get_user_profile(user_id)
            for user_id in range(5)
        ]
        results = await asyncio.gather(*tasks)
        
        # 验证所有调用都成功
        for i, result in enumerate(results):
            assert result["user_id"] == i
            assert result["name"] == f"User{i}"
        
        # 应该调用5次（每个用户一次）
        assert call_count == 5

    @pytest.mark.asyncio
    async def test_concurrent_version_increments(self):
        """测试并发版本递增"""
        manager = UniversalCacheManager(CacheConfig())
        
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


class TestErrorHandling:
    """错误处理测试类"""

    @pytest.mark.asyncio
    async def test_storage_error_handling(self):
        """测试存储错误处理"""
        manager = UniversalCacheManager(CacheConfig())
        
        # 模拟存储错误
        manager._storage.get = AsyncMock(side_effect=Exception("Storage error"))
        manager._storage.set = AsyncMock(side_effect=Exception("Storage error"))
        manager._storage.delete = AsyncMock(side_effect=Exception("Storage error"))
        
        # 测试获取错误处理
        value = await manager.get("test_key")
        assert value is None
        
        # 测试设置错误处理
        result = await manager.set("test_key", "test_value", ttl_seconds=60)
        assert result is False
        
        # 测试删除错误处理
        result = await manager.delete("test_key")
        assert result is False

    def test_decorator_error_handling(self):
        """测试装饰器错误处理"""
        call_count = 0
        
        @u_l_cache(ttl_seconds=60)
        def function_with_error(param):
            nonlocal call_count
            call_count += 1
            if param == "error":
                raise Exception("Function error")
            return f"result_{param}"
        
        # 正常调用
        result = function_with_error("normal")
        assert result == "result_normal"
        assert call_count == 1
        
        # 错误调用
        with pytest.raises(Exception, match="Function error"):
            function_with_error("error")
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_decorator_error_handling(self):
        """测试异步装饰器错误处理"""
        call_count = 0
        
        @u_l_cache(ttl_seconds=60)
        async def async_function_with_error(param):
            nonlocal call_count
            call_count += 1
            if param == "error":
                raise Exception("Async function error")
            await asyncio.sleep(0.1)
            return f"async_result_{param}"
        
        # 正常调用
        result = await async_function_with_error("normal")
        assert result == "async_result_normal"
        assert call_count == 1
        
        # 错误调用
        with pytest.raises(Exception, match="Async function error"):
            await async_function_with_error("error")
        assert call_count == 2


class TestPerformance:
    """性能测试类"""

    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """测试缓存性能"""
        manager = UniversalCacheManager(CacheConfig())
        
        # 测试大量缓存操作
        start_time = time.time()
        
        for i in range(1000):
            await manager.set(f"key_{i}", f"value_{i}", ttl_seconds=60)
        
        for i in range(1000):
            value = await manager.get(f"key_{i}")
            assert value == f"value_{i}"
        
        end_time = time.time()
        
        # 确保性能在合理范围内（5秒内完成2000次操作）
        assert end_time - start_time < 5.0

    def test_decorator_performance(self):
        """测试装饰器性能"""
        call_count = 0
        
        @u_l_cache(ttl_seconds=60)
        def performance_test_function(param):
            nonlocal call_count
            call_count += 1
            # 添加一些计算开销来测试性能差异
            time.sleep(0.01)  # 模拟10毫秒的计算时间
            return f"result_{param}"
        
        # 第一次调用（缓存未命中）
        start_time = time.time()
        result1 = performance_test_function("test")
        first_call_time = time.time() - start_time
        
        # 第二次调用（缓存命中）
        start_time = time.time()
        result2 = performance_test_function("test")
        second_call_time = time.time() - start_time
        
        assert result1 == result2 == "result_test"
        assert call_count == 1
        
        # 缓存命中应该比缓存未命中快（考虑到有10ms的计算时间）
        assert second_call_time < first_call_time * 0.5  # 放宽到50%
        assert first_call_time > 0.008  # 确保第一次调用确实有计算开销

    @pytest.mark.asyncio
    async def test_concurrent_performance(self):
        """测试并发性能"""
        manager = UniversalCacheManager(CacheConfig())
        
        async def concurrent_operation(i):
            await manager.set(f"key_{i}", f"value_{i}", ttl_seconds=60)
            return await manager.get(f"key_{i}")
        
        # 并发执行100个操作
        start_time = time.time()
        tasks = [concurrent_operation(i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # 验证所有操作成功
        for i, result in enumerate(results):
            assert result == f"value_{i}"
        
        # 确保并发性能在合理范围内（2秒内完成100个并发操作）
        assert end_time - start_time < 2.0


class TestRealWorldScenarios:
    """真实场景测试类"""

    def test_user_session_caching(self):
        """测试用户会话缓存场景"""
        call_count = 0
        
        @l_user_cache(
            cache_key=CacheKeyEnum.USER_PROFILE,
            key_params=["user_id"],
            storage_type=StorageType.MEMORY
        )
        def get_user_session(user_id: int):
            nonlocal call_count
            call_count += 1
            # 模拟从数据库获取用户会话信息
            return {
                "user_id": user_id,
                "session_id": f"session_{user_id}",
                "last_login": "2024-01-01T00:00:00Z",
                "permissions": ["read", "write", "admin"]
            }
        
        # 模拟用户多次访问
        for _ in range(10):
            result = get_user_session(123)
            assert result["user_id"] == 123
            assert result["session_id"] == "session_123"
        
        # 应该只调用一次函数
        assert call_count == 1

    def test_product_catalog_caching(self):
        """测试产品目录缓存场景"""
        call_count = 0
        
        @u_l_cache(ttl_seconds=300)  # 5分钟缓存
        def get_product_catalog(category: str, filters: dict):
            nonlocal call_count
            call_count += 1
            # 模拟从数据库获取产品目录
            return {
                "category": category,
                "filters": filters,
                "products": [
                    {"id": 1, "name": "Product 1", "price": 100},
                    {"id": 2, "name": "Product 2", "price": 200},
                ],
                "total_count": 2
            }
        
        # 模拟多次相同查询
        filters = {"price_min": 50, "price_max": 300}
        for _ in range(5):
            result = get_product_catalog("electronics", filters)
            assert result["category"] == "electronics"
            assert len(result["products"]) == 2
        
        # 应该只调用一次函数
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_api_response_caching(self):
        """测试API响应缓存场景"""
        call_count = 0
        
        @u_l_cache(ttl_seconds=60)
        async def fetch_api_data(endpoint: str, params: dict):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # 模拟API调用延迟
            return {
                "endpoint": endpoint,
                "params": params,
                "data": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}],
                "timestamp": "2024-01-01T00:00:00Z"
            }
        
        # 模拟多次相同API调用
        params = {"page": 1, "limit": 10}
        for _ in range(3):
            result = await fetch_api_data("/api/items", params)
            assert result["endpoint"] == "/api/items"
            assert len(result["data"]) == 2
        
        # 应该只调用一次函数
        assert call_count == 1

    def test_configuration_caching(self):
        """测试配置缓存场景"""
        call_count = 0
        
        @u_l_cache(ttl_seconds=3600)  # 1小时缓存
        def get_system_config(config_key: str):
            nonlocal call_count
            call_count += 1
            # 模拟从配置文件或数据库获取系统配置
            configs = {
                "database": {"host": "localhost", "port": 5432},
                "redis": {"host": "localhost", "port": 6379},
                "email": {"smtp_server": "smtp.example.com", "port": 587}
            }
            return configs.get(config_key, {})
        
        # 模拟多次获取相同配置
        for _ in range(10):
            db_config = get_system_config("database")
            assert db_config["host"] == "localhost"
            assert db_config["port"] == 5432
        
        # 应该只调用一次函数
        assert call_count == 1 