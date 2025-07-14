"""
测试缓存内存监控功能
"""

import asyncio
import time
import pytest
from unittest.mock import Mock, patch

from fn_cache import (
    UniversalCacheManager,
    CacheConfig,
    StorageType,
    CacheType,
    start_cache_memory_monitoring,
    stop_cache_memory_monitoring,
    get_cache_memory_usage,
    get_cache_memory_summary,
    register_cache_manager_for_monitoring,
    unregister_cache_manager_from_monitoring,
    MemoryUsageInfo,
    cached,
)
from fn_cache.decorators import cache_registry


class TestMemoryMonitoring:
    """测试内存监控功能"""

    def setup_method(self):
        """每个测试方法前的设置"""
        # 清理注册表
        cache_registry._registered_managers.clear()
        cache_registry._preload_able_funcs.clear()
        cache_registry._monitoring_enabled = False
        # 安全地取消监控任务
        if cache_registry._monitoring_task and not cache_registry._monitoring_task.done():
            try:
                cache_registry._monitoring_task.cancel()
            except RuntimeError:
                # 事件循环已关闭，忽略错误
                pass

    def test_register_manager(self):
        """测试注册缓存管理器"""
        manager = UniversalCacheManager()
        register_cache_manager_for_monitoring(manager)
        
        assert len(cache_registry._registered_managers) == 1
        assert manager in cache_registry._registered_managers.values()

    def test_unregister_manager(self):
        """测试注销缓存管理器"""
        manager = UniversalCacheManager()
        manager_id = f"{manager.config.storage_type.value}_{manager.config.prefix}_{id(manager)}"
        
        register_cache_manager_for_monitoring(manager)
        assert len(cache_registry._registered_managers) == 1
        
        unregister_cache_manager_from_monitoring(manager_id)
        assert len(cache_registry._registered_managers) == 0

    def test_memory_usage_calculation(self):
        """测试内存使用计算"""
        # 创建内存存储的缓存管理器
        config = CacheConfig(storage_type=StorageType.MEMORY, cache_type=CacheType.TTL)
        manager = UniversalCacheManager(config)
        
        # 添加一些测试数据
        manager.set_sync("key1", "value1", 300)
        manager.set_sync("key2", {"nested": "value2"}, 300)
        manager.set_sync("key3", [1, 2, 3], 300)
        
        register_cache_manager_for_monitoring(manager)
        
        memory_usage = get_cache_memory_usage()
        assert len(memory_usage) == 1
        
        info = memory_usage[0]
        assert info.storage_type == StorageType.MEMORY
        assert info.item_count == 3
        assert info.memory_bytes > 0
        assert info.memory_mb > 0

    def test_memory_summary(self):
        """测试内存使用摘要"""
        # 创建多个缓存管理器
        manager1 = UniversalCacheManager(CacheConfig(storage_type=StorageType.MEMORY))
        manager2 = UniversalCacheManager(CacheConfig(storage_type=StorageType.REDIS))
        
        # 添加测试数据
        manager1.set_sync("key1", "value1", 300)
        manager1.set_sync("key2", "value2", 300)
        
        register_cache_manager_for_monitoring(manager1)
        register_cache_manager_for_monitoring(manager2)
        
        summary = get_cache_memory_summary()
        
        assert summary["total_managers"] == 2
        assert summary["memory_storage_count"] == 1
        assert summary["other_storage_count"] == 1
        assert summary["total_items"] == 2
        assert summary["total_memory_mb"] > 0
        assert len(summary["managers"]) == 2

    def test_redis_storage_memory_usage(self):
        """测试Redis存储的内存使用计算"""
        config = CacheConfig(storage_type=StorageType.REDIS)
        manager = UniversalCacheManager(config)
        
        register_cache_manager_for_monitoring(manager)
        
        memory_usage = get_cache_memory_usage()
        assert len(memory_usage) == 1
        
        info = memory_usage[0]
        assert info.storage_type == StorageType.REDIS
        assert info.item_count == 0
        assert info.memory_bytes == 0
        assert info.memory_mb == 0.0

    def test_decorator_auto_registration(self):
        """测试装饰器自动注册缓存管理器"""
        @cached(storage_type=StorageType.MEMORY, ttl_seconds=300)
        def test_function(x):
            return x * 2
        
        # 装饰器会自动注册缓存管理器
        memory_usage = get_cache_memory_usage()
        assert len(memory_usage) == 1
        
        info = memory_usage[0]
        assert info.storage_type == StorageType.MEMORY
        assert info.cache_type == CacheType.TTL

    @pytest.mark.asyncio
    async def test_memory_monitoring_start_stop(self):
        """测试内存监控的启动和停止"""
        # 启动监控
        start_cache_memory_monitoring(interval_seconds=1)
        assert cache_registry._monitoring_enabled is True
        assert cache_registry._monitoring_task is not None
        assert not cache_registry._monitoring_task.done()
        
        # 等待一小段时间
        await asyncio.sleep(0.1)
        
        # 停止监控
        stop_cache_memory_monitoring()
        assert cache_registry._monitoring_enabled is False
        
        # 等待任务取消
        await asyncio.sleep(0.1)

    def test_memory_usage_info_pydantic(self):
        """测试MemoryUsageInfo pydantic模型"""
        info = MemoryUsageInfo(
            manager_id="test_manager",
            storage_type=StorageType.MEMORY,
            cache_type=CacheType.TTL,
            item_count=10,
            memory_bytes=1024,
            memory_mb=0.001,
            max_size=1000,
            prefix="test"
        )
        
        assert info.manager_id == "test_manager"
        assert info.storage_type == StorageType.MEMORY
        assert info.cache_type == CacheType.TTL
        assert info.item_count == 10
        assert info.memory_bytes == 1024
        assert info.memory_mb == 0.001
        assert info.max_size == 1000
        assert info.prefix == "test"

    def test_large_object_memory_estimation(self):
        """测试大对象的内存估算"""
        config = CacheConfig(storage_type=StorageType.MEMORY)
        manager = UniversalCacheManager(config)
        
        # 创建大对象
        large_dict = {f"key_{i}": f"value_{i}" * 100 for i in range(100)}
        large_list = [f"item_{i}" * 50 for i in range(50)]
        
        manager.set_sync("large_dict", large_dict, 300)
        manager.set_sync("large_list", large_list, 300)
        
        register_cache_manager_for_monitoring(manager)
        
        memory_usage = get_cache_memory_usage()
        assert len(memory_usage) == 1
        
        info = memory_usage[0]
        assert info.item_count == 2
        assert info.memory_bytes > 10000  # 应该占用相当多的内存

    def test_nested_object_memory_estimation(self):
        """测试嵌套对象的内存估算"""
        config = CacheConfig(storage_type=StorageType.MEMORY)
        manager = UniversalCacheManager(config)
        
        # 创建嵌套对象
        nested_obj = {
            "level1": {
                "level2": {
                    "level3": [1, 2, 3, {"nested": "value"}]
                }
            }
        }
        
        manager.set_sync("nested", nested_obj, 300)
        
        register_cache_manager_for_monitoring(manager)
        
        memory_usage = get_cache_memory_usage()
        assert len(memory_usage) == 1
        
        info = memory_usage[0]
        assert info.item_count == 1
        assert info.memory_bytes > 0

    def test_multiple_managers_memory_usage(self):
        """测试多个缓存管理器的内存使用"""
        # 创建多个内存缓存管理器
        manager1 = UniversalCacheManager(CacheConfig(storage_type=StorageType.MEMORY))
        manager2 = UniversalCacheManager(CacheConfig(storage_type=StorageType.MEMORY))
        manager3 = UniversalCacheManager(CacheConfig(storage_type=StorageType.REDIS))
        
        # 添加不同数量的数据
        for i in range(5):
            manager1.set_sync(f"key1_{i}", f"value1_{i}", 300)
        
        for i in range(10):
            manager2.set_sync(f"key2_{i}", f"value2_{i}", 300)
        
        register_cache_manager_for_monitoring(manager1)
        register_cache_manager_for_monitoring(manager2)
        register_cache_manager_for_monitoring(manager3)
        
        memory_usage = get_cache_memory_usage()
        assert len(memory_usage) == 3
        
        # 检查内存使用情况
        memory_managers = [info for info in memory_usage if info.storage_type == StorageType.MEMORY]
        redis_managers = [info for info in memory_usage if info.storage_type == StorageType.REDIS]
        
        assert len(memory_managers) == 2
        assert len(redis_managers) == 1
        
        # 检查项目数量
        item_counts = [info.item_count for info in memory_managers]
        assert 5 in item_counts
        assert 10 in item_counts


if __name__ == "__main__":
    pytest.main([__file__]) 