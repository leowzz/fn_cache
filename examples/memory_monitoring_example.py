"""
缓存内存监控功能使用示例

这个示例展示了如何使用 fn_cache 的内存监控功能来跟踪和管理缓存的内存使用情况。
"""

import asyncio
import time
import sys
import os

from fn_cache import (
    UniversalCacheManager,
    CacheConfig,
    StorageType,
    CacheType,
    cached,
    start_cache_memory_monitoring,
    stop_cache_memory_monitoring,
    get_cache_memory_usage,
    get_cache_memory_summary,
    register_cache_manager_for_monitoring,
    MemoryUsageInfo,
)


def example_basic_memory_monitoring():
    """基本内存监控示例"""
    print("=== 基本内存监控示例 ===")
    
    # 创建缓存管理器
    config = CacheConfig(storage_type=StorageType.MEMORY, cache_type=CacheType.TTL)
    manager = UniversalCacheManager(config)
    
    # 注册管理器进行监控
    register_cache_manager_for_monitoring(manager)
    
    # 添加一些测试数据
    for i in range(100):
        manager.set_sync(f"key_{i}", f"value_{i}" * 10, 300)
    
    # 获取内存使用情况
    memory_usage = get_cache_memory_usage()
    print(f"注册的管理器数量: {len(memory_usage)}")
    
    for info in memory_usage:
        print(f"管理器 {info.manager_id}:")
        print(f"  - 存储类型: {info.storage_type.value}")
        print(f"  - 缓存类型: {info.cache_type.value}")
        print(f"  - 项目数量: {info.item_count}")
        print(f"  - 内存使用: {info.memory_mb:.2f} MB")
        print(f"  - 最大容量: {info.max_size}")
        print()


def example_multiple_managers():
    """多个缓存管理器监控示例"""
    print("=== 多个缓存管理器监控示例 ===")
    
    # 创建多个不同类型的缓存管理器
    memory_manager = UniversalCacheManager(CacheConfig(storage_type=StorageType.MEMORY))
    redis_manager = UniversalCacheManager(CacheConfig(storage_type=StorageType.REDIS))
    
    # 注册管理器
    register_cache_manager_for_monitoring(memory_manager, "memory_cache")
    register_cache_manager_for_monitoring(redis_manager, "redis_cache")
    
    # 向内存缓存添加数据
    for i in range(50):
        memory_manager.set_sync(f"memory_key_{i}", {"data": f"value_{i}", "timestamp": time.time()}, 300)
    
    # 获取摘要信息
    summary = get_cache_memory_summary()
    print(f"总管理器数量: {summary['total_managers']}")
    print(f"内存存储管理器: {summary['memory_storage_count']}")
    print(f"其他存储管理器: {summary['other_storage_count']}")
    print(f"总项目数量: {summary['total_items']}")
    print(f"总内存使用: {summary['total_memory_mb']:.2f} MB")
    print()


def example_decorator_auto_monitoring():
    """装饰器自动监控示例（含大对象缓存）"""
    print("=== 装饰器自动监控示例 ===")
    
    # 普通小对象缓存
    @cached(storage_type=StorageType.MEMORY, ttl_seconds=600)
    def expensive_calculation(x: int) -> dict:
        """模拟昂贵的计算"""
        time.sleep(0.01)  # 模拟计算时间
        return {
            "input": x,
            "result": x * x,
            "timestamp": time.time(),
            "metadata": {"processed": True}
        }
    
    # 大对象1：大字符串（约50MB）
    @cached(storage_type=StorageType.MEMORY, ttl_seconds=600)
    def big_string_func():
        return "A" * (50 * 1024 * 1024)  # 50MB 字符串

    # 大对象2：大列表（约50MB）
    @cached(storage_type=StorageType.MEMORY, ttl_seconds=600)
    def big_list_func():
        return [123456] * (50 * 1024 * 1024 // 4)  # 50MB int列表（int约4字节）

    # 大对象3：大字典（约47MB）
    @cached(storage_type=StorageType.MEMORY, ttl_seconds=600)
    def big_dict_func():
        # 约47MB: 47*1024*1024/20 ≈ 2.46M项，每项key+value约20字节
        return {f"k{i}": i for i in range((47 * 1024 * 1024) // 20)}

    # 调用函数多次，填充缓存
    for i in range(10):
        result = expensive_calculation(i)
        print(f"计算结果 {i}: {result['result']}")
    
    # 调用大对象函数，填充缓存
    print("填充大对象缓存...")
    big_string_func()
    big_list_func()
    big_dict_func()
    print("大对象缓存已填充！")
    
    # 检查内存使用情况
    memory_usage = get_cache_memory_usage()
    summary = get_cache_memory_summary()
    print(f"自动注册的管理器数量: {len(memory_usage)}")
    print(f"内存监控摘要: 总项目数={summary['total_items']}，总内存={summary['total_memory_mb']:.2f} MB")
    
    for info in memory_usage:
        if info.storage_type == StorageType.MEMORY:
            print(f"装饰器缓存管理器: {info.item_count} 个项目, {info.memory_mb:.2f} MB")
    print()


async def example_periodic_monitoring():
    """定期监控示例"""
    print("=== 定期监控示例 ===")
    
    # 创建缓存管理器并添加数据
    manager = UniversalCacheManager(CacheConfig(storage_type=StorageType.MEMORY))
    register_cache_manager_for_monitoring(manager)
    
    # 启动定期监控（每2秒报告一次）
    start_cache_memory_monitoring(interval_seconds=2)
    print("已启动定期内存监控（每2秒报告一次）")
    
    # 模拟应用运行，持续添加数据
    for i in range(5):
        # 添加新数据
        for j in range(20):
            manager.set_sync(f"batch_{i}_key_{j}", f"data_{i}_{j}" * 5, 300)
        
        print(f"批次 {i+1}: 添加了 20 个新项目")
        
        # 等待监控报告
        await asyncio.sleep(3)
    
    # 停止监控
    stop_cache_memory_monitoring()
    print("已停止定期内存监控")
    print()


def example_memory_analysis():
    """内存分析示例"""
    print("=== 内存分析示例 ===")
    
    # 创建不同大小的数据来测试内存估算
    manager = UniversalCacheManager(CacheConfig(storage_type=StorageType.MEMORY))
    register_cache_manager_for_monitoring(manager)
    
    # 小对象
    manager.set_sync("small", "hello", 300)
    
    # 中等对象
    medium_data = {"user": "john", "age": 30, "city": "beijing"}
    manager.set_sync("medium", medium_data, 300)
    
    # 大对象
    large_data = {
        "users": [{"id": i, "name": f"user_{i}", "data": "x" * 100} for i in range(100)],
        "metadata": {"total": 100, "processed": True}
    }
    manager.set_sync("large", large_data, 300)
    
    # 获取详细的内存使用信息
    memory_usage = get_cache_memory_usage()
    
    for info in memory_usage:
        print(f"缓存项目分析:")
        print(f"  - 总项目数: {info.item_count}")
        print(f"  - 总内存: {info.memory_bytes} 字节 ({info.memory_mb:.2f} MB)")
        print(f"  - 平均每项: {info.memory_bytes // info.item_count if info.item_count > 0 else 0} 字节")
        print(f"  - 内存使用率: {(info.item_count / info.max_size * 100):.1f}%")
    print()


async def main():
    """主函数"""
    print("fn_cache 内存监控功能示例")
    print("=" * 50)
    
    # 运行各种示例
    example_basic_memory_monitoring()
    example_multiple_managers()
    example_decorator_auto_monitoring()
    await example_periodic_monitoring()
    example_memory_analysis()
    
    print("示例完成！")


if __name__ == "__main__":
    asyncio.run(main()) 