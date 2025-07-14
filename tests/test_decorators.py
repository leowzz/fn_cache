"""
装饰器测试
"""

import asyncio
import time
from enum import Enum
from unittest.mock import Mock, patch, AsyncMock

import pytest

from fn_cache import (
    cached, CacheKeyEnum, CacheType, StorageType,
    invalidate_all_caches, preload_all_caches
)
from fn_cache.decorators import _CacheRegistry


class CacheKeyEnum(str, Enum):
    """测试用缓存键枚举"""
    USER_INFO = "user:info:{user_id}"
    USER_SETTINGS = "user:settings:{user_id}:{setting_type}"
    PRODUCT_INFO = "product:info:{product_id}"

    def format(self, **kwargs) -> str:
        """格式化缓存键，替换模板中的参数"""
        return self.value.format(**kwargs)


class TestULCacheDecorator:
    """通用轻量缓存装饰器测试类"""

    def test_init_with_default_params(self):
        """测试使用默认参数初始化"""
        decorator = cached()
        assert decorator.config.cache_type == CacheType.TTL
        assert decorator.config.storage_type == StorageType.MEMORY
        assert decorator.config.ttl_seconds == 600
        assert decorator.config.max_size == 1000
        assert decorator.key_func is None
        assert decorator.preload_provider is None

    def test_init_with_custom_params(self):
        """测试使用自定义参数初始化"""

        def custom_key_func(*args, **kwargs):
            return f"custom:{args[0]}"

        def preload_provider():
            return [((1,), {}), ((2,), {})]

        decorator = cached(
            cache_type=CacheType.LRU,
            storage_type=StorageType.MEMORY,
            ttl_seconds=300,
            max_size=500,
            key_func=custom_key_func,
            prefix="custom:",
            preload_provider=preload_provider
        )

        assert decorator.config.cache_type == CacheType.LRU
        assert decorator.config.storage_type == StorageType.MEMORY
        assert decorator.config.ttl_seconds == 300
        assert decorator.config.max_size == 500
        assert decorator.config.prefix == "custom:"
        assert decorator.key_func == custom_key_func
        assert decorator.preload_provider == preload_provider

    def test_sync_function_caching(self):
        """测试同步函数缓存"""
        call_count = 0

        @cached(ttl_seconds=60)
        def test_function(param1, param2="default"):
            nonlocal call_count
            call_count += 1
            return f"result_{param1}_{param2}"

        # 第一次调用
        result1 = test_function("test1")
        assert result1 == "result_test1_default"
        assert call_count == 1

        # 第二次调用（应该从缓存返回）
        result2 = test_function("test1")
        assert result2 == "result_test1_default"
        assert call_count == 1  # 调用次数不应该增加

        # 不同参数应该重新调用
        result3 = test_function("test2", "custom")
        assert result3 == "result_test2_custom"
        assert call_count == 2



    def test_sync_function_with_custom_key_func(self):
        """测试带自定义键函数的同步函数"""
        call_count = 0

        def custom_key_func(*args, **kwargs):
            return f"custom_key_{args[0]}_{kwargs.get('param2', 'default')}"

        @cached(key_func=custom_key_func)
        def test_function(param1, param2="default"):
            nonlocal call_count
            call_count += 1
            return f"result_{param1}_{param2}"

        # 第一次调用
        result1 = test_function("test1", param2="custom")
        assert result1 == "result_test1_custom"
        assert call_count == 1

        # 相同键应该从缓存返回
        result2 = test_function("test1", param2="custom")
        assert result2 == "result_test1_custom"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_function_caching(self):
        """测试异步函数缓存"""
        call_count = 0

        @cached(ttl_seconds=60)
        async def test_async_function(param1, param2="default"):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # 模拟异步操作
            return f"async_result_{param1}_{param2}"

        # 第一次调用
        result1 = await test_async_function("test1")
        assert result1 == "async_result_test1_default"
        assert call_count == 1

        # 第二次调用（应该从缓存返回）
        result2 = await test_async_function("test1")
        assert result2 == "async_result_test1_default"
        assert call_count == 1  # 调用次数不应该增加

    @pytest.mark.asyncio
    async def test_async_function_with_complex_params(self):
        """测试异步函数复杂参数"""
        call_count = 0

        @cached(ttl_seconds=60)
        async def test_async_function(param1, param2, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            return f"result_{param1}_{param2}_{kwargs.get('extra', 'default')}"

        # 第一次调用
        result1 = await test_async_function("test1", "value1", extra="custom")
        assert result1 == "result_test1_value1_custom"
        assert call_count == 1

        # 相同参数应该从缓存返回
        result2 = await test_async_function("test1", "value1", extra="custom")
        assert result2 == "result_test1_value1_custom"
        assert call_count == 1

    def test_none_result_caching(self):
        """测试None结果缓存"""
        call_count = 0

        @cached(ttl_seconds=60)
        def test_function(param):
            nonlocal call_count
            call_count += 1
            return None

        # 第一次调用
        result1 = test_function("test")
        assert result1 is None
        assert call_count == 1

        # 第二次调用（None值不应该被缓存）
        result2 = test_function("test")
        assert result2 is None
        assert call_count == 2  # 应该重新调用

    def test_cache_key_generation(self):
        """测试缓存键生成"""

        @cached()
        def test_function(param1, param2="default"):
            return f"result_{param1}_{param2}"

        # 调用函数以触发缓存键生成
        test_function("test1", "custom")

        # 验证缓存键格式
        # 这里我们无法直接访问生成的键，但可以通过多次调用来验证缓存工作

    def test_concurrent_calls(self):
        """测试并发调用"""
        call_count = 0

        @cached(ttl_seconds=60)
        def test_function(param):
            nonlocal call_count
            call_count += 1
            time.sleep(0.1)  # 模拟耗时操作
            return f"result_{param}"

        # 并发调用相同参数
        import threading

        def call_function():
            return test_function("test")

        threads = [threading.Thread(target=call_function) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # 应该只调用一次函数
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_sync_cache_clear(self):
        """测试同步函数缓存清除功能"""
        call_count = 0

        @cached(ttl_seconds=60)
        def test_function(param):
            nonlocal call_count
            call_count += 1
            return f"result_{param}"

        # 第一次调用，缓存未命中
        result1 = test_function("a")
        assert result1 == "result_a"
        assert call_count == 1

        # 第二次调用，缓存命中
        result2 = test_function("a")
        assert result2 == "result_a"
        assert call_count == 1

        # 清除缓存（异步）
        await test_function.cache.clear()

        # 第三次调用，缓存应失效
        result3 = test_function("a")
        assert result3 == "result_a"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_cache_clear(self):
        """测试异步函数缓存清除功能"""
        call_count = 0

        @cached(ttl_seconds=60)
        async def test_async_function(param):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return f"async_result_{param}"

        # 第一次调用，缓存未命中
        result1 = await test_async_function("b")
        assert result1 == "async_result_b"
        assert call_count == 1

        # 第二次调用，缓存命中
        result2 = await test_async_function("b")
        assert result2 == "async_result_b"
        assert call_count == 1

        # 清除缓存
        await test_async_function.cache.clear()

        # 第三次调用，缓存应失效
        result3 = await test_async_function("b")
        assert result3 == "async_result_b"
        assert call_count == 2



class TestCacheRegistry:
    """缓存注册表测试类"""

    def test_init(self):
        """测试初始化"""
        registry = _CacheRegistry()
        assert registry._preload_able_funcs == []

    def test_register(self):
        """测试注册函数"""
        registry = _CacheRegistry()
        preload_info = {
            'func': lambda: None,
            'manager': Mock(),
            'key_builder': lambda *args, **kwargs: "key",
            'preload_provider': lambda: [],
            'ttl_seconds': 60
        }

        registry.register(preload_info)
        assert len(registry._preload_able_funcs) == 1
        assert registry._preload_able_funcs[0] == preload_info

    @pytest.mark.asyncio
    async def test_preload_all_memory_storage(self):
        """测试内存存储预加载"""
        registry = _CacheRegistry()

        # 使用真实的缓存管理器
        from fn_cache import UniversalCacheManager, CacheConfig
        real_manager = UniversalCacheManager(CacheConfig(storage_type=StorageType.MEMORY))

        # 模拟函数
        call_count = 0

        def test_func(param):
            nonlocal call_count
            call_count += 1
            return f"result_{param}"

        def key_builder(param):
            return f"key_{param}"

        def preload_provider():
            return [((1,), {}), ((2,), {})]

        preload_info = {
            'func': test_func,
            'manager': real_manager,
            'key_builder': key_builder,
            'preload_provider': preload_provider,
            'ttl_seconds': 60
        }

        registry.register(preload_info)

        # 执行预加载
        await registry.preload_all()

        # 验证函数被调用
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_preload_all_with_error(self):
        """测试预加载时出错"""
        registry = _CacheRegistry()

        # 模拟缓存管理器
        mock_manager = Mock()
        mock_manager.config.storage_type = StorageType.MEMORY

        def preload_provider():
            raise Exception("Preload error")

        preload_info = {
            'func': lambda: None,
            'manager': mock_manager,
            'key_builder': lambda *args, **kwargs: "key",
            'preload_provider': preload_provider,
            'ttl_seconds': 60
        }

        registry.register(preload_info)

        # 执行预加载（应该不会抛出异常）
        await registry.preload_all()

    @pytest.mark.asyncio
    async def test_iterate_params_sync(self):
        """测试同步参数迭代"""
        registry = _CacheRegistry()

        params = [((1,), {}), ((2,), {})]
        async for item in registry._iterate_params(params):
            assert item in params

    @pytest.mark.asyncio
    async def test_iterate_params_async(self):
        """测试异步参数迭代"""
        registry = _CacheRegistry()

        async def async_params():
            yield ((1,), {})
            yield ((2,), {})

        count = 0
        async for item in registry._iterate_params(async_params()):
            count += 1
            assert isinstance(item, tuple)

        assert count == 2

    @pytest.mark.asyncio
    async def test_execute_func_sync(self):
        """测试同步函数执行"""
        registry = _CacheRegistry()

        def sync_func(param):
            return f"sync_result_{param}"

        result = await registry._execute_func(sync_func, "test")
        assert result == "sync_result_test"

    @pytest.mark.asyncio
    async def test_execute_func_async(self):
        """测试异步函数执行"""
        registry = _CacheRegistry()

        async def async_func(param):
            await asyncio.sleep(0.1)
            return f"async_result_{param}"

        result = await registry._execute_func(async_func, "test")
        assert result == "async_result_test"


class TestGlobalFunctions:
    """全局函数测试类"""

    @pytest.mark.asyncio
    async def test_preload_all_caches(self):
        """测试预加载所有缓存"""
        with patch('fn_cache.decorators.cache_registry') as mock_registry:
            mock_registry.preload_all = AsyncMock()
            await preload_all_caches()
            mock_registry.preload_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_all_caches(self):
        """测试使所有缓存失效"""
        with patch('fn_cache.decorators.UniversalCacheManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.invalidate_all = AsyncMock(return_value=True)

            await invalidate_all_caches()

            # 验证调用了invalidate_all方法
            mock_manager.invalidate_all.assert_called_once()


