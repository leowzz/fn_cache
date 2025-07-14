#!/usr/bin/env python3
"""
全局缓存开关示例

演示如何使用全局开关功能来一键控制所有缓存操作。
"""

import asyncio
import time
from fn_cache.decorators import cached, enable_global_cache, disable_global_cache, is_global_cache_enabled
from fn_cache.decorators import enable_all_registered_caches, disable_all_registered_caches, get_all_cache_status


# 示例1：使用默认配置的缓存装饰器
@cached(ttl_seconds=60)
def expensive_calculation_sync(x: int, y: int) -> int:
    """模拟耗时的同步计算"""
    print(f"执行同步计算: {x} + {y}")
    time.sleep(1)  # 模拟耗时操作
    return x + y


@cached(ttl_seconds=60)
async def expensive_calculation_async(x: int, y: int) -> int:
    """模拟耗时的异步计算"""
    print(f"执行异步计算: {x} * {y}")
    await asyncio.sleep(1)  # 模拟耗时操作
    return x * y


# 示例2：使用自定义配置的缓存装饰器
@cached(
    cache_type="TTL",
    storage_type="MEMORY", 
    ttl_seconds=30,
    prefix="custom:"
)
def custom_cache_function(name: str) -> str:
    """使用自定义配置的缓存函数"""
    print(f"执行自定义缓存函数: {name}")
    time.sleep(0.5)
    return f"Hello, {name}!"


def demo_basic_usage():
    """演示基本使用"""
    print("=== 基本使用演示 ===")
    
    # 第一次调用，会执行计算并缓存结果
    print("\n1. 第一次调用（缓存未命中）:")
    result1 = expensive_calculation_sync(10, 20)
    print(f"结果: {result1}")
    
    # 第二次调用，会从缓存获取结果
    print("\n2. 第二次调用（缓存命中）:")
    result2 = expensive_calculation_sync(10, 20)
    print(f"结果: {result2}")
    
    # 禁用全局缓存
    print("\n3. 禁用全局缓存:")
    disable_global_cache()
    print(f"全局缓存状态: {is_global_cache_enabled()}")
    
    # 再次调用，会直接执行函数，跳过缓存
    print("\n4. 禁用缓存后的调用:")
    result3 = expensive_calculation_sync(10, 20)
    print(f"结果: {result3}")
    
    # 重新启用全局缓存
    print("\n5. 重新启用全局缓存:")
    enable_global_cache()
    print(f"全局缓存状态: {is_global_cache_enabled()}")
    
    # 再次调用，会从缓存获取结果
    print("\n6. 重新启用后的调用:")
    result4 = expensive_calculation_sync(10, 20)
    print(f"结果: {result4}")


async def demo_async_usage():
    """演示异步使用"""
    print("\n=== 异步使用演示 ===")
    
    # 第一次调用
    print("\n1. 第一次异步调用:")
    result1 = await expensive_calculation_async(5, 6)
    print(f"结果: {result1}")
    
    # 第二次调用（缓存命中）
    print("\n2. 第二次异步调用（缓存命中）:")
    result2 = await expensive_calculation_async(5, 6)
    print(f"结果: {result2}")
    
    # 禁用缓存
    print("\n3. 禁用全局缓存:")
    disable_global_cache()
    
    # 再次调用
    print("\n4. 禁用缓存后的异步调用:")
    result3 = await expensive_calculation_async(5, 6)
    print(f"结果: {result3}")


def demo_multiple_managers():
    """演示多个缓存管理器的控制"""
    print("\n=== 多管理器控制演示 ===")
    
    # 调用不同的缓存函数，创建多个管理器
    print("\n1. 创建多个缓存管理器:")
    result1 = expensive_calculation_sync(1, 2)
    result2 = custom_cache_function("Alice")
    result3 = custom_cache_function("Bob")
    
    # 查看所有缓存状态
    print("\n2. 查看所有缓存管理器状态:")
    status = get_all_cache_status()
    for manager_id, enabled in status.items():
        print(f"  {manager_id}: {'启用' if enabled else '禁用'}")
    
    # 禁用所有缓存
    print("\n3. 禁用所有已注册的缓存:")
    disable_all_registered_caches()
    
    # 再次查看状态
    print("\n4. 禁用后的状态:")
    status = get_all_cache_status()
    for manager_id, enabled in status.items():
        print(f"  {manager_id}: {'启用' if enabled else '禁用'}")
    
    # 重新启用所有缓存
    print("\n5. 重新启用所有缓存:")
    enable_all_registered_caches()
    
    # 最终状态
    print("\n6. 重新启用后的状态:")
    status = get_all_cache_status()
    for manager_id, enabled in status.items():
        print(f"  {manager_id}: {'启用' if enabled else '禁用'}")


def demo_decorator_control():
    """演示装饰器级别的控制"""
    print("\n=== 装饰器级别控制演示 ===")
    
    # 正常调用
    print("\n1. 正常调用（使用缓存）:")
    result1 = expensive_calculation_sync(100, 200)
    print(f"结果: {result1}")
    
    # 使用装饰器参数控制
    print("\n2. 使用装饰器参数禁用读取缓存:")
    result2 = expensive_calculation_sync(100, 200, cache_read=False)
    print(f"结果: {result2}")
    
    print("\n3. 使用装饰器参数禁用写入缓存:")
    result3 = expensive_calculation_sync(100, 200, cache_write=False)
    print(f"结果: {result3}")
    
    print("\n4. 同时禁用读写缓存:")
    result4 = expensive_calculation_sync(100, 200, cache_read=False, cache_write=False)
    print(f"结果: {result4}")


async def main():
    """主函数"""
    print("全局缓存开关功能演示")
    print("=" * 50)
    
    # 基本使用演示
    demo_basic_usage()
    
    # 异步使用演示
    await demo_async_usage()
    
    # 多管理器控制演示
    demo_multiple_managers()
    
    # 装饰器级别控制演示
    demo_decorator_control()
    
    print("\n" + "=" * 50)
    print("演示完成！")


if __name__ == "__main__":
    asyncio.run(main()) 