"""
装饰器测试
"""

import asyncio
import time
from enum import Enum
from unittest.mock import Mock, patch, AsyncMock

import pytest

from l_cache import (
    u_l_cache, CacheKeyEnum, CacheType, StorageType,
    invalidate_all_caches, invalidate_user_cache, preload_all_caches
)
from l_cache.decorators import _CacheRegistry


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
        decorator = u_l_cache()
        assert decorator.config.cache_type == CacheType.TTL
        assert decorator.config.storage_type == StorageType.MEMORY
        assert decorator.config.ttl_seconds == 600
        assert decorator.config.max_size == 1000
        assert decorator.key_func is None
        assert decorator.key_params is None
        assert decorator.preload_provider is None

    def test_init_with_custom_params(self):
        """测试使用自定义参数初始化"""

        def custom_key_func(*args, **kwargs):
            return f"custom:{args[0]}"

        def preload_provider():
            return [((1,), {}), ((2,), {})]

        decorator = u_l_cache(
            cache_type=CacheType.LRU,
            storage_type=StorageType.MEMORY,
            ttl_seconds=300,
            max_size=500,
            key_func=custom_key_func,
            key_params=["param1"],
            prefix="custom:",
            preload_provider=preload_provider
        )

        assert decorator.config.cache_type == CacheType.LRU
        assert decorator.config.storage_type == StorageType.MEMORY
        assert decorator.config.ttl_seconds == 300
        assert decorator.config.max_size == 500
        assert decorator.config.prefix == "custom:"
        assert decorator.key_func == custom_key_func
        assert decorator.key_params == ["param1"]
        assert decorator.preload_provider == preload_provider

    def test_sync_function_caching(self):
        """测试同步函数缓存"""
        call_count = 0

        @u_l_cache(ttl_seconds=60)
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

    def test_sync_function_with_key_params(self):
        """测试带键参数的同步函数"""
        call_count = 0

        @u_l_cache(key_params=["param1"])
        def test_function(param1, param2, param3="default"):
            nonlocal call_count
            call_count += 1
            return f"result_{param1}_{param2}_{param3}"

        # 第一次调用
        result1 = test_function("test1", "value1", "custom1")
        assert result1 == "result_test1_value1_custom1"
        assert call_count == 1

        # 相同param1，不同param2（应该从缓存返回）
        result2 = test_function("test1", "value2", "custom2")
        assert result2 == "result_test1_value1_custom1"  # 返回缓存值
        assert call_count == 1

        # 不同param1应该重新调用
        result3 = test_function("test2", "value1", "custom1")
        assert result3 == "result_test2_value1_custom1"
        assert call_count == 2

    def test_sync_function_with_custom_key_func(self):
        """测试带自定义键函数的同步函数"""
        call_count = 0

        def custom_key_func(*args, **kwargs):
            return f"custom_key_{args[0]}_{kwargs.get('param2', 'default')}"

        @u_l_cache(key_func=custom_key_func)
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

        @u_l_cache(ttl_seconds=60)
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

        @u_l_cache(ttl_seconds=60)
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

        @u_l_cache(ttl_seconds=60)
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

        @u_l_cache()
        def test_function(param1, param2="default"):
            return f"result_{param1}_{param2}"

        # 调用函数以触发缓存键生成
        test_function("test1", "custom")

        # 验证缓存键格式
        # 这里我们无法直接访问生成的键，但可以通过多次调用来验证缓存工作

    def test_concurrent_calls(self):
        """测试并发调用"""
        call_count = 0

        @u_l_cache(ttl_seconds=60)
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


class TestLUserCacheDecorator:
    """用户缓存装饰器测试类"""

    def test_init_with_default_params(self):
        """测试使用默认参数初始化"""
        decorator = u_l_cache(cache_key_enum=CacheKeyEnum.USER_INFO)
        assert decorator.cache_key_enum == CacheKeyEnum.USER_INFO
        assert decorator.config.storage_type == StorageType.MEMORY
        assert decorator.key_params is None
        assert decorator.config.prefix == "l_cache:"
        assert decorator.user_id_param == "user_id"

    def test_init_with_custom_params(self):
        """测试使用自定义参数初始化"""

        def make_expire_sec_func(user_id):
            return 300 if user_id == "vip" else 60

        decorator = u_l_cache(
            cache_key_enum=CacheKeyEnum.USER_SETTINGS,
            storage_type=StorageType.MEMORY,
            make_expire_sec_func=make_expire_sec_func,
            key_params=["user_id", "setting_type"],
            prefix="custom:",
            user_id_param="uid"
        )

        assert decorator.cache_key_enum == CacheKeyEnum.USER_SETTINGS
        assert decorator.config.storage_type == StorageType.MEMORY
        assert decorator.make_expire_sec_func == make_expire_sec_func
        assert decorator.key_params == ["user_id", "setting_type"]
        assert decorator.config.prefix == "custom:"
        assert decorator.user_id_param == "uid"

    def test_sync_function_caching(self):
        """测试同步函数缓存"""
        call_count = 0

        @u_l_cache(
            cache_key_enum=CacheKeyEnum.USER_INFO,
            key_params=["user_id"],
            storage_type=StorageType.MEMORY
        )
        def get_user_info(user_id: int):
            nonlocal call_count
            call_count += 1
            return {"user_id": user_id, "name": f"User{user_id}"}

        # 第一次调用
        result1 = get_user_info(123)
        assert result1["user_id"] == 123
        assert result1["name"] == "User123"
        assert call_count == 1

        # 第二次调用（应该从缓存返回）
        result2 = get_user_info(123)
        assert result2["user_id"] == 123
        assert call_count == 1

        # 不同用户ID应该重新调用
        result3 = get_user_info(456)
        assert result3["user_id"] == 456
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_function_caching(self):
        """测试异步函数缓存"""
        call_count = 0

        @u_l_cache(
            cache_key_enum=CacheKeyEnum.USER_INFO,
            key_params=["user_id"],
            storage_type=StorageType.MEMORY
        )
        async def get_user_info_async(user_id: int):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            return {"user_id": user_id, "name": f"User{user_id}"}

        # 第一次调用
        result1 = await get_user_info_async(123)
        assert result1["user_id"] == 123
        assert call_count == 1

        # 第二次调用（应该从缓存返回）
        result2 = await get_user_info_async(123)
        assert result2["user_id"] == 123
        assert call_count == 1

    def test_function_with_multiple_key_params(self):
        """测试多键参数函数"""
        call_count = 0

        @u_l_cache(
            cache_key_enum=CacheKeyEnum.USER_SETTINGS,
            key_params=["user_id", "setting_type"],
            storage_type=StorageType.MEMORY
        )
        def get_user_setting(user_id: int, setting_type: str):
            nonlocal call_count
            call_count += 1
            return {"user_id": user_id, "setting": setting_type, "value": "setting_value"}

        # 第一次调用
        result1 = get_user_setting(123, "theme")
        assert result1["setting"] == "theme"
        assert call_count == 1

        # 相同参数应该从缓存返回
        result2 = get_user_setting(123, "theme")
        assert result2["setting"] == "theme"
        assert call_count == 1

        # 不同setting_type应该重新调用
        result3 = get_user_setting(123, "language")
        assert result3["setting"] == "language"
        assert call_count == 2

    def test_function_with_custom_expire_func(self):
        """测试自定义过期时间函数"""
        call_count = 0

        def make_expire_sec_func(user_id):
            return 300 if user_id == "vip" else 60

        @u_l_cache(
            cache_key_enum=CacheKeyEnum.USER_INFO,
            key_params=["user_id"],
            make_expire_sec_func=make_expire_sec_func,
            storage_type=StorageType.MEMORY
        )
        def get_user_info(user_id: str):
            nonlocal call_count
            call_count += 1
            return {"user_id": user_id, "vip": user_id == "vip"}

        # 调用函数
        result1 = get_user_info("vip")
        assert result1["vip"] is True

        assert call_count == 1

        result2 = get_user_info("normal")
        assert result2["vip"] is False
        assert call_count == 2

    def test_cache_key_building(self):
        """测试缓存键构建"""

        @u_l_cache(
            cache_key_enum=CacheKeyEnum.USER_INFO,
            key_params=["user_id"],
            storage_type=StorageType.MEMORY
        )
        def get_user_info(user_id: int):
            return {"user_id": user_id}

        # 调用函数以触发缓存键构建
        get_user_info(123)

        # 验证缓存键格式
        # 这里我们无法直接访问生成的键，但可以通过多次调用来验证缓存工作

    def test_none_result_handling(self):
        """测试None结果处理"""
        call_count = 0

        @u_l_cache(
            cache_key_enum=CacheKeyEnum.USER_INFO,
            key_params=["user_id"],
            storage_type=StorageType.MEMORY
        )
        def get_user_info(user_id: int):
            nonlocal call_count
            call_count += 1
            return None

        # 第一次调用
        result1 = get_user_info(123)
        assert result1 is None
        assert call_count == 1

        # 第二次调用（None值不应该被缓存）
        result2 = get_user_info(123)
        assert result2 is None
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
        from l_cache import UniversalCacheManager, CacheConfig
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
        with patch('l_cache.decorators.cache_registry') as mock_registry:
            mock_registry.preload_all = AsyncMock()
            await preload_all_caches()
            mock_registry.preload_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_all_caches(self):
        """测试使所有缓存失效"""
        with patch('l_cache.decorators.UniversalCacheManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.invalidate_all = AsyncMock(return_value=True)

            await invalidate_all_caches()

            # 验证调用了invalidate_all方法
            mock_manager.invalidate_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_user_cache(self):
        """测试使用户缓存失效"""
        with patch('l_cache.decorators.UniversalCacheManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.invalidate_user_cache = AsyncMock(return_value=True)

            await invalidate_user_cache("user123")

            # 验证调用了invalidate_user_cache方法
            mock_manager.invalidate_user_cache.assert_called_once_with("user123")

    @pytest.mark.asyncio
    async def test_u_l_cache_invalidate_cache(self):
        """测试用户缓存装饰器的失效方法"""
        with patch('l_cache.decorators.UniversalCacheManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.delete = AsyncMock(return_value=True)

            await u_l_cache.invalidate_cache(
                user_id="user123",
                cache_key_enum=CacheKeyEnum.USER_INFO,
                key_params={"user_id": 123}
            )

            # 验证调用了delete方法
            mock_manager.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_u_l_cache_invalidate_cache_without_key_params(self):
        """测试用户缓存装饰器的失效方法（无键参数）"""
        # 使用一个不需要参数的缓存键进行测试
        with patch('l_cache.decorators.UniversalCacheManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.delete = AsyncMock(return_value=True)

            # 应该会抛出KeyError，因为USER_INFO需要user_id参数
            with pytest.raises(KeyError):
                await u_l_cache.invalidate_cache(
                    user_id="user123",
                    cache_key_enum=CacheKeyEnum.USER_INFO
                )
