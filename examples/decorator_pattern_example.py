"""
装饰器模式示例 - 展示新的 cached 装饰器使用方法
"""

import asyncio
import time
from typing import Dict, Any

from l_cache.decorators import cached
from l_cache.enums import CacheType, StorageType, CacheKeyEnum
from l_cache.config import DEFAULT_PREFIX


# 示例1: 基本使用
@cached(
    cache_type=CacheType.TTL,
    storage_type=StorageType.MEMORY,
    ttl_seconds=60,
    max_size=100
)
async def get_user_data(user_id: int) -> Dict[str, Any]:
    """获取用户数据 - 基本缓存示例"""
    print(f"Fetching user data for user_id: {user_id}")
    await asyncio.sleep(1)  # 模拟网络请求
    return {"user_id": user_id, "name": f"User_{user_id}", "email": f"user{user_id}@example.com"}


# 示例2: 使用缓存控制参数
@cached(
    cache_type=CacheType.TTL,
    storage_type=StorageType.MEMORY,
    ttl_seconds=300,
    max_size=50
)
async def get_product_info(product_id: int, cache_read: bool = True, cache_write: bool = True) -> Dict[str, Any]:
    """获取产品信息 - 支持缓存控制"""
    print(f"Fetching product info for product_id: {product_id}")
    await asyncio.sleep(0.5)  # 模拟网络请求
    return {"product_id": product_id, "name": f"Product_{product_id}", "price": 99.99}


# 示例3: 使用缓存键枚举
class ProductCacheKeys(CacheKeyEnum):
    PRODUCT_INFO = "product:info:{product_id}"
    PRODUCT_PRICE = "product:price:{product_id}"


@cached(
    cache_type=CacheType.TTL,
    storage_type=StorageType.MEMORY,
    ttl_seconds=600,
    cache_key_enum=ProductCacheKeys.PRODUCT_INFO,
    key_params=["product_id"]
)
async def get_product_details(product_id: int) -> Dict[str, Any]:
    """获取产品详细信息 - 使用缓存键枚举"""
    print(f"Fetching product details for product_id: {product_id}")
    await asyncio.sleep(1)
    return {
        "product_id": product_id,
        "name": f"Product_{product_id}",
        "description": f"Detailed description for product {product_id}",
        "price": 99.99,
        "category": "Electronics"
    }


# 示例4: 异步写入控制
@cached(
    cache_type=CacheType.TTL,
    storage_type=StorageType.MEMORY,
    ttl_seconds=120
)
async def get_analytics_data(date: str, wait_for_write: bool = True) -> Dict[str, Any]:
    """获取分析数据 - 支持异步写入控制"""
    print(f"Fetching analytics data for date: {date}")
    await asyncio.sleep(2)  # 模拟复杂计算
    return {
        "date": date,
        "page_views": 1000,
        "unique_visitors": 500,
        "conversion_rate": 0.05
    }


# 示例5: 同步函数缓存
@cached(
    cache_type=CacheType.LRU,
    storage_type=StorageType.MEMORY,
    max_size=200
)
def calculate_fibonacci(n: int) -> int:
    """计算斐波那契数 - 同步函数缓存示例"""
    print(f"Calculating fibonacci({n})")
    if n <= 1:
        return n
    return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)


async def main():
    """主函数 - 演示各种缓存模式"""
    print("=== 装饰器模式示例 ===\n")
    
    # 示例1: 基本缓存
    print("1. 基本缓存示例:")
    result1 = await get_user_data(123)
    print(f"结果: {result1}")
    result1_cached = await get_user_data(123)  # 应该从缓存获取
    print(f"缓存结果: {result1_cached}\n")
    
    # 示例2: 缓存控制
    print("2. 缓存控制示例:")
    result2 = await get_product_info(456)
    print(f"结果: {result2}")
    # 禁用缓存读取
    result2_no_cache = await get_product_info(456, cache_read=False)
    print(f"无缓存结果: {result2_no_cache}\n")
    
    # 示例3: 缓存键枚举
    print("3. 缓存键枚举示例:")
    result3 = await get_product_details(789)
    print(f"结果: {result3}")
    result3_cached = await get_product_details(789)  # 应该从缓存获取
    print(f"缓存结果: {result3_cached}\n")
    
    # 示例4: 异步写入控制
    print("4. 异步写入控制示例:")
    result4 = await get_analytics_data("2024-01-01")
    print(f"结果: {result4}")
    # 不等待写入完成
    result4_async = await get_analytics_data("2024-01-02", wait_for_write=False)
    print(f"异步写入结果: {result4_async}\n")
    
    # 示例5: 同步函数缓存
    print("5. 同步函数缓存示例:")
    fib_result = calculate_fibonacci(10)
    print(f"斐波那契(10): {fib_result}")
    fib_result_cached = calculate_fibonacci(10)  # 应该从缓存获取
    print(f"缓存斐波那契(10): {fib_result_cached}\n")
    
    # 演示缓存统计
    print("6. 缓存统计信息:")
    from l_cache.decorators import get_cache_statistics
    stats = get_cache_statistics()
    print(f"缓存统计: {stats}")


if __name__ == "__main__":
    asyncio.run(main()) 