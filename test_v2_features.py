#!/usr/bin/env python3
"""
测试 fn_cache v2.0 新功能

验证以下功能：
1. 多种序列化格式支持
2. 缓存统计功能
3. 内存监控功能
4. 更灵活的配置选项
"""

import asyncio
import time
import sys
import os
import pytest
from enum import Enum

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fn_cache import (
    cached, StorageType, CacheType, SerializerType,
    UniversalCacheManager, CacheConfig, get_cache_statistics, reset_cache_statistics,
    start_cache_memory_monitoring, get_cache_memory_usage, preload_all_caches
)


def test_serializers():
    """测试不同序列化器"""
    print("1. 测试不同序列化器:")
    
    @cached(
        storage_type=StorageType.MEMORY,
        serializer_type=SerializerType.JSON,
        ttl_seconds=300
    )
    def test_json_serializer(user_id: int):
        print(f"JSON序列化: 获取用户 {user_id} 数据")
        return {"user_id": user_id, "name": f"用户_{user_id}", "type": "json"}

    @cached(
        storage_type=StorageType.MEMORY,
        serializer_type=SerializerType.PICKLE,
        ttl_seconds=300
    )
    def test_pickle_serializer(user_id: int):
        print(f"Pickle序列化: 获取用户 {user_id} 数据")
        return {"user_id": user_id, "name": f"用户_{user_id}", "type": "pickle"}

    result1 = test_json_serializer(1)
    result1_cached = test_json_serializer(1)  # 应该从缓存返回
    print(f"JSON结果: {result1}")
    
    result2 = test_pickle_serializer(2)
    result2_cached = test_pickle_serializer(2)  # 应该从缓存返回
    print(f"Pickle结果: {result2}")


@pytest.mark.asyncio
async def test_user_cache():
    """测试用户级别缓存"""
    print("\n2. 测试用户级别缓存:")
    
    def user_info_key_func(user_id: int):
        return f"test:user:info:{user_id}"
    
    def user_stats_key_func(user_id: int, tenant_id: str):
        return f"test:user:stats:{user_id}:{tenant_id}"
    
    @cached(
        key_func=user_info_key_func,
        storage_type=StorageType.MEMORY
    )
    async def test_user_cache_func(user_id: int):
        print(f"用户缓存: 获取用户 {user_id} 信息")
        await asyncio.sleep(0.1)
        return {"user_id": user_id, "vip": user_id % 2 == 0}

    @cached(
        key_func=user_stats_key_func,
        storage_type=StorageType.MEMORY
    )
    async def test_multi_param_cache_func(user_id: int, tenant_id: str):
        print(f"多参数缓存: 获取用户 {user_id} 在租户 {tenant_id} 的统计")
        await asyncio.sleep(0.1)
        return {"user_id": user_id, "tenant_id": tenant_id, "stats": {"visits": 100}}

    vip_info1 = await test_user_cache_func(123)
    vip_info2 = await test_user_cache_func(123)  # 应该从缓存返回
    print(f"VIP信息: {vip_info1}")
    
    permissions1 = await test_multi_param_cache_func(456, "tenant_a")
    permissions2 = await test_multi_param_cache_func(456, "tenant_a")  # 应该从缓存返回
    print(f"权限: {permissions1}")


# 测试3: 缓存管理器
@pytest.mark.asyncio
async def test_cache_manager():
    print("\n=== 测试缓存管理器 ===")
    
    config = CacheConfig(
        storage_type=StorageType.MEMORY,
        serializer_type=SerializerType.JSON,
        ttl_seconds=60,
        enable_statistics=True
    )
    
    manager = UniversalCacheManager(config)
    
    # 测试基本操作
    await manager.set("test_key", {"data": "test_value"}, ttl_seconds=30)
    result = await manager.get("test_key")
    print(f"缓存管理器测试: {result}")
    
    # 测试用户级别版本控制
    await manager.set("user_key", {"user_data": "value"}, user_id="123")
    user_result = await manager.get("user_key", user_id="123")
    print(f"用户级别缓存: {user_result}")


# 测试4: 缓存统计
@pytest.mark.asyncio
async def test_statistics():
    print("\n=== 测试缓存统计 ===")
    
    # 重置统计
    reset_cache_statistics()
    
    @cached(
        storage_type=StorageType.MEMORY,
        serializer_type=SerializerType.JSON,
        ttl_seconds=300
    )
    def test_json_serializer(user_id: int):
        print(f"JSON序列化: 获取用户 {user_id} 数据")
        return {"user_id": user_id, "name": f"用户_{user_id}", "type": "json"}

    @cached(
        storage_type=StorageType.MEMORY,
        serializer_type=SerializerType.PICKLE,
        ttl_seconds=300
    )
    def test_pickle_serializer(user_id: int):
        print(f"Pickle序列化: 获取用户 {user_id} 数据")
        return {"user_id": user_id, "name": f"用户_{user_id}", "type": "pickle"}

    def user_info_key_func(user_id: int):
        return f"test:user:info:{user_id}"
    
    def user_stats_key_func(user_id: int, tenant_id: str):
        return f"test:user:stats:{user_id}:{tenant_id}"
    
    @cached(
        key_func=user_info_key_func,
        storage_type=StorageType.MEMORY
    )
    async def test_user_cache_func(user_id: int):
        print(f"用户缓存: 获取用户 {user_id} 信息")
        await asyncio.sleep(0.1)
        return {"user_id": user_id, "vip": user_id % 2 == 0}

    @cached(
        key_func=user_stats_key_func,
        storage_type=StorageType.MEMORY
    )
    async def test_multi_param_cache_func(user_id: int, tenant_id: str):
        print(f"多参数缓存: 获取用户 {user_id} 在租户 {tenant_id} 的统计")
        await asyncio.sleep(0.1)
        return {"user_id": user_id, "tenant_id": tenant_id, "stats": {"visits": 100}}
    
    # 执行一些缓存操作
    for i in range(3):
        test_json_serializer(i)
        test_pickle_serializer(i)
        await test_user_cache_func(i)
        await test_multi_param_cache_func(i, "tenant_a")
    
    # 获取统计信息
    stats = get_cache_statistics()
    print("缓存统计信息:")
    for cache_id, cache_stats in stats.items():
        print(f"  {cache_id}:")
        print(f"    命中率: {cache_stats.get('hit_rate', 0):.2%}")
        print(f"    总请求数: {cache_stats.get('total_requests', 0)}")
        print(f"    平均响应时间: {cache_stats.get('avg_response_time', 0):.4f}s")


# 测试5: 内存监控
@pytest.mark.asyncio
async def test_memory_monitoring():
    print("\n=== 测试内存监控 ===")
    
    # 启动内存监控
    start_cache_memory_monitoring(interval_seconds=5)
    
    @cached(
        storage_type=StorageType.MEMORY,
        serializer_type=SerializerType.JSON,
        ttl_seconds=300
    )
    def test_json_serializer(user_id: int):
        print(f"JSON序列化: 获取用户 {user_id} 数据")
        return {"user_id": user_id, "name": f"用户_{user_id}", "type": "json"}

    @cached(
        storage_type=StorageType.MEMORY,
        serializer_type=SerializerType.PICKLE,
        ttl_seconds=300
    )
    def test_pickle_serializer(user_id: int):
        print(f"Pickle序列化: 获取用户 {user_id} 数据")
        return {"user_id": user_id, "name": f"用户_{user_id}", "type": "pickle"}
    
    # 执行一些缓存操作
    for i in range(5):
        test_json_serializer(i)
        test_pickle_serializer(i)
    
    # 等待监控运行
    await asyncio.sleep(1)
    
    # 获取内存使用情况
    memory_usage = get_cache_memory_usage()
    print("内存使用情况:")
    for usage in memory_usage:
        print(f"  {usage.manager_id}:")
        print(f"    存储类型: {usage.storage_type}")
        print(f"    缓存类型: {usage.cache_type}")
        print(f"    项目数: {usage.item_count}")
        print(f"    内存使用: {usage.memory_mb:.2f} MB")


# 测试6: 缓存预热
@pytest.mark.asyncio
async def test_preload():
    print("\n=== 测试缓存预热 ===")
    
    def user_ids_provider():
        for user_id in range(1, 4):
            yield (user_id,), {}
    
    @cached(
        storage_type=StorageType.MEMORY,
        preload_provider=user_ids_provider,
        ttl_seconds=300
    )
    def get_user_name(user_id: int):
        print(f"从数据库获取用户 {user_id} 姓名")
        return f"用户_{user_id}"
    
    # 执行预热
    await preload_all_caches()
    
    # 验证预热结果
    for user_id in range(1, 4):
        result = get_user_name(user_id)
        print(f"预热后获取用户 {user_id}: {result}")


# 测试7: 动态TTL
@pytest.mark.asyncio
async def test_dynamic_ttl():
    print("\n=== 测试动态TTL ===")
    
    def make_expire_sec_func(result):
        # 根据结果动态设置TTL
        if isinstance(result, dict) and result.get("vip"):
            return 3600  # VIP用户缓存1小时
        return 300  # 普通用户缓存5分钟
    
    @cached(
        storage_type=StorageType.MEMORY,
        make_expire_sec_func=make_expire_sec_func,
        ttl_seconds=300  # 默认TTL
    )
    async def get_user_profile(user_id: int):
        print(f"获取用户 {user_id} 资料")
        await asyncio.sleep(0.1)
        return {"user_id": user_id, "vip": user_id % 2 == 0, "name": f"用户_{user_id}"}
    
    # 测试VIP用户（应该缓存1小时）
    vip_user = await get_user_profile(100)
    print(f"VIP用户资料: {vip_user}")
    
    # 测试普通用户（应该缓存5分钟）
    normal_user = await get_user_profile(101)
    print(f"普通用户资料: {normal_user}")


# 测试8: 缓存控制
@pytest.mark.asyncio
async def test_cache_control():
    print("\n=== 测试缓存控制 ===")
    
    call_count = 0
    
    @cached(
        storage_type=StorageType.MEMORY,
        ttl_seconds=300
    )
    async def controlled_function(param: str, cache_read: bool = True, cache_write: bool = True):
        nonlocal call_count
        call_count += 1
        print(f"函数被调用: {param} (调用次数: {call_count})")
        await asyncio.sleep(0.1)
        return f"结果_{param}"
    
    # 正常调用
    result1 = await controlled_function("test1")
    print(f"正常调用结果: {result1}")
    
    # 禁用缓存读取
    result2 = await controlled_function("test1", cache_read=False)
    print(f"禁用缓存读取结果: {result2}")
    
    # 禁用缓存写入
    result3 = await controlled_function("test2", cache_write=False)
    print(f"禁用缓存写入结果: {result3}")
    
    # 再次调用test2，应该重新计算
    result4 = await controlled_function("test2")
    print(f"再次调用test2结果: {result4}")
    
    print(f"总调用次数: {call_count}")


# 测试9: 缓存清理
@pytest.mark.asyncio
async def test_cache_cleanup():
    print("\n=== 测试缓存清理 ===")
    
    @cached(
        storage_type=StorageType.MEMORY,
        ttl_seconds=300
    )
    async def cleanup_test_function(param: str):
        print(f"清理测试函数被调用: {param}")
        await asyncio.sleep(0.1)
        return f"清理结果_{param}"
    
    # 第一次调用
    result1 = await cleanup_test_function("test")
    print(f"第一次调用结果: {result1}")
    
    # 第二次调用（应该从缓存返回）
    result2 = await cleanup_test_function("test")
    print(f"第二次调用结果: {result2}")
    
    # 清理缓存
    await cleanup_test_function.cache.clear()
    print("缓存已清理")
    
    # 第三次调用（应该重新计算）
    result3 = await cleanup_test_function("test")
    print(f"清理后调用结果: {result3}")


@pytest.mark.asyncio
async def test_all_features():
    """测试所有功能"""
    print("\n=== 开始测试所有功能 ===")
    
    # 测试序列化器
    test_serializers()
    
    # 测试用户缓存
    await test_user_cache()
    
    # 测试缓存管理器
    await test_cache_manager()
    
    # 测试缓存统计
    await test_statistics()
    
    # 测试内存监控
    await test_memory_monitoring()
    
    # 测试缓存预热
    await test_preload()
    
    # 测试动态TTL
    await test_dynamic_ttl()
    
    # 测试缓存控制
    await test_cache_control()
    
    # 测试缓存清理
    await test_cache_cleanup()
    
    print("\n=== 所有功能测试完成 ===")


if __name__ == "__main__":
    asyncio.run(test_all_features()) 