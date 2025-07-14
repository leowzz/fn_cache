"""
L-Cache v2.0 使用示例

展示优化后的 l_cache 库的新功能，包括：
- 多种序列化格式支持
- 缓存统计和性能监控
- 更灵活的配置选项
- 更好的错误处理
"""

import asyncio
import time
from typing import Dict, Any

from . import (
    u_l_cache, l_user_cache, CacheKeyEnum, StorageType, CacheType, SerializerType,
    UniversalCacheManager, CacheConfig, get_cache_statistics, reset_cache_statistics,
    start_cache_memory_monitoring, get_cache_memory_usage
)


# 示例1: 使用不同序列化器的缓存
@u_l_cache(
    storage_type=StorageType.MEMORY,
    serializer_type=SerializerType.JSON,
    ttl_seconds=300
)
def get_user_profile_json(user_id: int) -> Dict[str, Any]:
    """使用JSON序列化的用户资料缓存"""
    print(f"从数据库获取用户 {user_id} 的资料 (JSON序列化)...")
    time.sleep(0.1)  # 模拟数据库查询
    return {
        "user_id": user_id,
        "name": f"用户_{user_id}",
        "email": f"user{user_id}@example.com",
        "profile": {
            "age": 25 + user_id % 20,
            "city": "北京",
            "interests": ["编程", "阅读", "旅行"]
        }
    }


@u_l_cache(
    storage_type=StorageType.MEMORY,
    serializer_type=SerializerType.PICKLE,
    ttl_seconds=300
)
def get_user_profile_pickle(user_id: int) -> Dict[str, Any]:
    """使用Pickle序列化的用户资料缓存"""
    print(f"从数据库获取用户 {user_id} 的资料 (Pickle序列化)...")
    time.sleep(0.1)  # 模拟数据库查询
    return {
        "user_id": user_id,
        "name": f"用户_{user_id}",
        "email": f"user{user_id}@example.com",
        "profile": {
            "age": 25 + user_id % 20,
            "city": "北京",
            "interests": ["编程", "阅读", "旅行"]
        }
    }


# 示例2: 缓存键枚举和用户级别版本控制
class UserCacheKeyEnum(CacheKeyEnum):
    """用户相关缓存键枚举"""
    USER_VIP_INFO = "user:vip:info:{user_id}"
    USER_PERMISSIONS = "user:permissions:{user_id}:{tenant_id}"
    USER_PREFERENCES = "user:preferences:{user_id}"


@l_user_cache(
    cache_key=UserCacheKeyEnum.USER_VIP_INFO,
    key_params=["user_id"],
    storage_type=StorageType.REDIS,
    make_expire_sec_func=lambda result: 3600 if result.get("is_vip") else 1800
)
async def get_user_vip_info(user_id: int) -> Dict[str, Any]:
    """获取用户VIP信息，支持动态过期时间"""
    print(f"从数据库获取用户 {user_id} 的VIP信息...")
    await asyncio.sleep(0.1)  # 模拟异步数据库查询
    
    is_vip = user_id % 3 == 0
    return {
        "user_id": user_id,
        "is_vip": is_vip,
        "vip_level": "gold" if is_vip else "none",
        "expire_date": "2024-12-31" if is_vip else None
    }


@l_user_cache(
    cache_key=UserCacheKeyEnum.USER_PERMISSIONS,
    key_params=["user_id", "tenant_id"],
    storage_type=StorageType.REDIS
)
async def get_user_permissions(user_id: int, tenant_id: str) -> list:
    """获取用户权限，支持多参数缓存键"""
    print(f"从数据库获取用户 {user_id} 在租户 {tenant_id} 的权限...")
    await asyncio.sleep(0.1)  # 模拟异步数据库查询
    
    # 模拟权限数据
    base_permissions = ["read", "write"]
    if user_id % 2 == 0:
        base_permissions.append("admin")
    if tenant_id == "premium":
        base_permissions.append("premium_feature")
    
    return base_permissions


# 示例3: 直接使用缓存管理器
async def demonstrate_cache_manager():
    """演示直接使用缓存管理器"""
    print("\n=== 缓存管理器示例 ===")
    
    # 创建不同配置的缓存管理器
    memory_config = CacheConfig(
        storage_type=StorageType.MEMORY,
        serializer_type=SerializerType.JSON,
        ttl_seconds=300,
        enable_statistics=True
    )
    
    redis_config = CacheConfig(
        storage_type=StorageType.REDIS,
        serializer_type=SerializerType.MESSAGEPACK,
        ttl_seconds=600,
        enable_statistics=True,
        redis_config={
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "decode_responses": True,
            "socket_timeout": 1.0,
            "socket_connect_timeout": 1.0,
        }
    )
    
    memory_manager = UniversalCacheManager(memory_config)
    redis_manager = UniversalCacheManager(redis_config)
    
    # 使用内存缓存管理器
    await memory_manager.set("test_key", {"data": "test_value"}, ttl_seconds=60)
    cached_value = await memory_manager.get("test_key")
    print(f"内存缓存结果: {cached_value}")
    
    # 使用Redis缓存管理器
    try:
        await redis_manager.set("redis_test_key", {"data": "redis_value"}, ttl_seconds=60)
        redis_cached_value = await redis_manager.get("redis_test_key")
        print(f"Redis缓存结果: {redis_cached_value}")
    except Exception as e:
        print(f"Redis连接失败: {e}")


# 示例4: 缓存统计功能
async def demonstrate_statistics():
    """演示缓存统计功能"""
    print("\n=== 缓存统计示例 ===")
    
    # 执行一些缓存操作
    for i in range(5):
        get_user_profile_json(i)
        await get_user_vip_info(i)
        await get_user_permissions(i, "default")
    
    # 获取统计信息
    stats = get_cache_statistics()
    print("缓存统计信息:")
    for cache_id, cache_stats in stats.items():
        print(f"  {cache_id}:")
        print(f"    命中率: {cache_stats.get('hit_rate', 0):.2%}")
        print(f"    总请求数: {cache_stats.get('total_requests', 0)}")
        print(f"    平均响应时间: {cache_stats.get('avg_response_time', 0):.4f}s")
        print(f"    错误数: {cache_stats.get('errors', 0)}")


# 示例5: 内存监控功能
async def demonstrate_memory_monitoring():
    """演示内存监控功能"""
    print("\n=== 内存监控示例 ===")
    
    # 启动内存监控
    start_cache_memory_monitoring(interval_seconds=10)  # 每10秒监控一次
    
    # 执行一些缓存操作
    for i in range(10):
        get_user_profile_json(i)
        get_user_profile_pickle(i)
    
    # 等待一段时间让监控运行
    await asyncio.sleep(2)
    
    # 获取内存使用情况
    memory_usage = get_cache_memory_usage()
    print("内存使用情况:")
    for usage in memory_usage:
        print(f"  {usage.manager_id}:")
        print(f"    存储类型: {usage.storage_type}")
        print(f"    缓存类型: {usage.cache_type}")
        print(f"    项目数: {usage.item_count}")
        print(f"    内存使用: {usage.memory_mb:.2f} MB")


# 示例6: 批量操作和预热
async def demonstrate_batch_operations():
    """演示批量操作和缓存预热"""
    print("\n=== 批量操作示例 ===")
    
    # 定义数据提供者
    def user_ids_provider():
        """提供用户ID列表用于预热"""
        for user_id in range(1, 6):
            yield (user_id,), {}
    
    # 使用预加载功能的缓存
    @u_l_cache(
        storage_type=StorageType.MEMORY,
        preload_provider=user_ids_provider,
        ttl_seconds=300
    )
    def get_user_name(user_id: int) -> str:
        print(f"从数据库获取用户 {user_id} 的姓名...")
        time.sleep(0.1)  # 模拟数据库查询
        return f"用户_{user_id}"
    
    # 预加载缓存
    from . import preload_all_caches
    await preload_all_caches()
    
    # 验证预加载结果
    for i in range(1, 6):
        result = get_user_name(i)  # 应该直接从缓存返回
        print(f"用户 {i} 姓名: {result}")


async def main():
    """运行所有示例"""
    print("=== L-Cache v2.0 功能演示 ===\n")
    
    # 示例1: 不同序列化器
    print("1. 不同序列化器示例:")
    print("JSON序列化:")
    result1 = get_user_profile_json(1)
    result1_cached = get_user_profile_json(1)  # 应该从缓存返回
    print(f"结果: {result1}")
    
    print("\nPickle序列化:")
    result2 = get_user_profile_pickle(2)
    result2_cached = get_user_profile_pickle(2)  # 应该从缓存返回
    print(f"结果: {result2}")
    
    # 示例2: 用户级别缓存
    print("\n2. 用户级别缓存示例:")
    vip_info1 = await get_user_vip_info(123)
    vip_info2 = await get_user_vip_info(123)  # 应该从缓存返回
    print(f"VIP信息: {vip_info1}")
    
    permissions1 = await get_user_permissions(456, "tenant_a")
    permissions2 = await get_user_permissions(456, "tenant_a")  # 应该从缓存返回
    print(f"权限: {permissions1}")
    
    # 示例3: 缓存管理器
    await demonstrate_cache_manager()
    
    # 示例4: 缓存统计
    await demonstrate_statistics()
    
    # 示例5: 内存监控
    await demonstrate_memory_monitoring()
    
    # 示例6: 批量操作
    await demonstrate_batch_operations()
    
    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    asyncio.run(main()) 