"""
测试新的装饰器模式
"""

import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock

from fn_cache.decorators import cached
from fn_cache.enums import CacheType, StorageType, CacheKeyEnum
from fn_cache.config import DEFAULT_PREFIX


class TestDecoratorPattern:
    """测试装饰器模式"""

    def test_basic_async_decorator(self):
        """测试基本异步装饰器"""
        call_count = 0
        
        @cached(
            cache_type=CacheType.TTL,
            storage_type=StorageType.MEMORY,
            ttl_seconds=60
        )
        async def test_func(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2
        
        async def run_test():
            # 第一次调用
            result1 = await test_func(5)
            assert result1 == 10
            assert call_count == 1
            
            # 第二次调用应该从缓存获取
            result2 = await test_func(5)
            assert result2 == 10
            assert call_count == 1  # 调用次数不应该增加
        
        asyncio.run(run_test())

    def test_basic_sync_decorator(self):
        """测试基本同步装饰器"""
        call_count = 0
        
        @cached(
            cache_type=CacheType.LRU,
            storage_type=StorageType.MEMORY,
            max_size=100
        )
        def test_func(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 3
        
        # 第一次调用
        result1 = test_func(4)
        assert result1 == 12
        assert call_count == 1
        
        # 第二次调用应该从缓存获取
        result2 = test_func(4)
        assert result2 == 12
        assert call_count == 1  # 调用次数不应该增加

    def test_cache_read_control(self):
        """测试缓存读取控制"""
        call_count = 0
        
        @cached(
            cache_type=CacheType.TTL,
            storage_type=StorageType.MEMORY,
            ttl_seconds=60
        )
        async def test_func(x: int, cache_read: bool = True) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2
        
        async def run_test():
            # 第一次调用
            result1 = await test_func(5)
            assert result1 == 10
            assert call_count == 1
            
            # 禁用缓存读取
            result2 = await test_func(5, cache_read=False)
            assert result2 == 10
            assert call_count == 2  # 应该再次调用函数
        
        asyncio.run(run_test())

    def test_cache_write_control(self):
        """测试缓存写入控制"""
        call_count = 0
        
        @cached(
            cache_type=CacheType.TTL,
            storage_type=StorageType.MEMORY,
            ttl_seconds=60
        )
        async def test_func(x: int, cache_write: bool = True) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2
        
        async def run_test():
            # 第一次调用，写入缓存
            result1 = await test_func(5)
            assert result1 == 10
            assert call_count == 1
            
            # 禁用缓存写入
            result2 = await test_func(6, cache_write=False)
            assert result2 == 12
            assert call_count == 2
            
            # 再次调用6，应该重新计算（因为之前没有写入缓存）
            result3 = await test_func(6)
            assert result3 == 12
            assert call_count == 3
        
        asyncio.run(run_test())

    def test_wait_for_write_control(self):
        """测试异步写入控制"""
        call_count = 0
        
        @cached(
            cache_type=CacheType.TTL,
            storage_type=StorageType.MEMORY,
            ttl_seconds=60
        )
        async def test_func(x: int, wait_for_write: bool = True) -> int:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # 模拟异步操作
            return x * 2
        
        async def run_test():
            start_time = time.time()
            
            # 等待写入完成
            result1 = await test_func(5, wait_for_write=True)
            elapsed1 = time.time() - start_time
            assert result1 == 10
            assert elapsed1 >= 0.1  # 应该等待写入完成
            
            # 不等待写入完成
            start_time = time.time()
            result2 = await test_func(6, wait_for_write=False)
            elapsed2 = time.time() - start_time
            assert result2 == 12
            assert elapsed2 < 0.15  # 不应该等待写入完成，但给一些容差
        
        asyncio.run(run_test())



    def test_decorator_attributes(self):
        """测试装饰器属性"""
        @cached(
            cache_type=CacheType.TTL,
            storage_type=StorageType.MEMORY,
            ttl_seconds=60
        )
        async def test_func(x: int) -> int:
            return x * 2
        
        # 检查装饰器是否正确设置了cache属性
        assert hasattr(test_func, 'cache')
        assert test_func.cache is not None

    def test_make_expire_sec_func(self):
        """测试动态过期时间函数"""
        call_count = 0
        
        def make_expire_sec(result: int) -> int:
            return result  # 根据结果动态设置过期时间
        
        @cached(
            cache_type=CacheType.TTL,
            storage_type=StorageType.MEMORY,
            ttl_seconds=60,
            make_expire_sec_func=make_expire_sec
        )
        async def test_func(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2
        
        async def run_test():
            # 第一次调用
            result1 = await test_func(5)
            assert result1 == 10
            assert call_count == 1
            
            # 第二次调用应该从缓存获取
            result2 = await test_func(5)
            assert result2 == 10
            assert call_count == 1
        
        asyncio.run(run_test())




if __name__ == "__main__":
    pytest.main([__file__]) 