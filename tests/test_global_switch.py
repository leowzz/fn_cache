#!/usr/bin/env python3
"""
全局缓存开关功能测试
"""

import pytest
import asyncio
import time
from fn_cache.decorators import (
    cached, 
    enable_global_cache, 
    disable_global_cache, 
    is_global_cache_enabled,
    enable_all_registered_caches,
    disable_all_registered_caches,
    get_all_cache_status
)
from fn_cache.manager import UniversalCacheManager


# 测试用的缓存函数
@cached(ttl_seconds=60)
def sync_add(x: int, y: int) -> int:
    """测试同步函数"""
    time.sleep(0.1)  # 模拟耗时操作
    return x + y


@cached(ttl_seconds=60)
async def async_mul(x: int, y: int) -> int:
    """测试异步函数"""
    await asyncio.sleep(0.1)  # 模拟耗时操作
    return x * y


class TestGlobalCacheSwitch:
    """全局缓存开关测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        # 确保缓存是启用状态
        enable_global_cache()

    def test_enable_disable_cache(self):
        """测试启用和禁用缓存"""
        # 初始状态应该是启用的
        assert is_global_cache_enabled() is True
        
        # 禁用缓存
        disable_global_cache()
        assert is_global_cache_enabled() is False
        
        # 重新启用缓存
        enable_global_cache()
        assert is_global_cache_enabled() is True

    def test_sync_function_with_cache_disabled(self):
        """测试禁用缓存时同步函数的行为"""
        # 第一次调用，启用缓存
        start_time = time.time()
        result1 = sync_add(10, 20)
        time1 = time.time() - start_time
        assert result1 == 30
        
        # 第二次调用，应该从缓存获取（更快）
        start_time = time.time()
        result2 = sync_add(10, 20)
        time2 = time.time() - start_time
        assert result2 == 30
        assert time2 < time1  # 缓存命中应该更快
        
        # 禁用缓存
        disable_global_cache()
        
        # 再次调用，应该重新执行函数
        start_time = time.time()
        result3 = sync_add(10, 20)
        time3 = time.time() - start_time
        assert result3 == 30
        assert time3 >= 0.1  # 应该重新执行，需要时间
        
        # 重新启用缓存
        enable_global_cache()
        
        # 再次调用，应该从缓存获取
        start_time = time.time()
        result4 = sync_add(10, 20)
        time4 = time.time() - start_time
        assert result4 == 30
        assert time4 < time3  # 缓存命中应该更快

    @pytest.mark.asyncio
    async def test_async_function_with_cache_disabled(self):
        """测试禁用缓存时异步函数的行为"""
        # 第一次调用，启用缓存
        start_time = time.time()
        result1 = await async_mul(5, 6)
        time1 = time.time() - start_time
        assert result1 == 30
        
        # 第二次调用，应该从缓存获取（更快）
        start_time = time.time()
        result2 = await async_mul(5, 6)
        time2 = time.time() - start_time
        assert result2 == 30
        assert time2 < time1  # 缓存命中应该更快
        
        # 禁用缓存
        disable_global_cache()
        
        # 再次调用，应该重新执行函数
        start_time = time.time()
        result3 = await async_mul(5, 6)
        time3 = time.time() - start_time
        assert result3 == 30
        assert time3 >= 0.1  # 应该重新执行，需要时间
        
        # 重新启用缓存
        enable_global_cache()
        
        # 再次调用，应该从缓存获取
        start_time = time.time()
        result4 = await async_mul(5, 6)
        time4 = time.time() - start_time
        assert result4 == 30
        assert time4 < time3  # 缓存命中应该更快

    def test_manager_direct_control(self):
        """测试直接控制缓存管理器"""
        manager = UniversalCacheManager()
        
        # 初始状态
        assert manager.is_cache_enabled is True
        
        # 禁用
        disable_global_cache()
        assert manager.is_cache_enabled is False
        
        # 重新启用
        enable_global_cache()
        assert manager.is_cache_enabled is True

    def test_multiple_managers_control(self):
        """测试多个缓存管理器的控制"""
        # 创建多个缓存管理器（通过调用不同的缓存函数）
        sync_add(1, 2)
        sync_add(3, 4)
        
        # 获取状态
        status = get_all_cache_status()
        assert len(status) >= 1
        
        # 所有管理器应该都是启用状态
        for manager_id, enabled in status.items():
            assert enabled is True
        
        # 禁用所有缓存
        disable_all_registered_caches()
        
        # 检查状态
        status = get_all_cache_status()
        for manager_id, enabled in status.items():
            assert enabled is False
        
        # 重新启用所有缓存
        enable_all_registered_caches()
        
        # 检查状态
        status = get_all_cache_status()
        for manager_id, enabled in status.items():
            assert enabled is True

    def test_cache_operations_when_disabled(self):
        """测试禁用缓存时的缓存操作"""
        manager = UniversalCacheManager()
        
        # 设置一个缓存值
        manager.set_sync("test_key", "test_value", 60)
        
        # 获取缓存值
        value = manager.get_sync("test_key")
        assert value == "test_value"
        
        # 禁用缓存
        disable_global_cache()
        
        # 获取操作应该返回None
        value = manager.get_sync("test_key")
        assert value is None
        
        # 设置操作应该返回False
        success = manager.set_sync("test_key2", "test_value2", 60)
        assert success is False
        
        # 删除操作应该返回False
        success = manager.delete_sync("test_key")
        assert success is False
        
        # 重新启用缓存
        enable_global_cache()
        
        # 设置新的缓存值
        success = manager.set_sync("test_key3", "test_value3", 60)
        assert success is True
        
        # 获取缓存值
        value = manager.get_sync("test_key3")
        assert value == "test_value3"

    @pytest.mark.asyncio
    async def test_async_cache_operations_when_disabled(self):
        """测试禁用缓存时的异步缓存操作"""
        manager = UniversalCacheManager()
        
        # 设置一个缓存值
        await manager.set("test_key", "test_value", 60)
        
        # 获取缓存值
        value = await manager.get("test_key")
        assert value == "test_value"
        
        # 禁用缓存
        disable_global_cache()
        
        # 获取操作应该返回None
        value = await manager.get("test_key")
        assert value is None
        
        # 设置操作应该返回False
        success = await manager.set("test_key2", "test_value2", 60)
        assert success is False
        
        # 删除操作应该返回False
        success = await manager.delete("test_key")
        assert success is False
        
        # 重新启用缓存
        enable_global_cache()
        
        # 设置新的缓存值
        success = await manager.set("test_key3", "test_value3", 60)
        assert success is True
        
        # 获取缓存值
        value = await manager.get("test_key3")
        assert value == "test_value3"


if __name__ == "__main__":
    pytest.main([__file__]) 