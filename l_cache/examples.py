"""
L-Cache 使用示例

本文件展示了 l_cache 库的各种使用方法和最佳实践。
"""

import asyncio
import time
from typing import Dict, List, Any

from . import (
    u_l_cache,
    u_l_cache,
    CacheKeyEnum,
    CacheType,
    StorageType,
    UniversalCacheManager,
    CacheConfig,
    preload_all_caches,
    invalidate_all_caches,
    invalidate_user_cache,
)


# 定义缓存键枚举
class UserCacheKeyEnum(CacheKeyEnum):
    """用户相关缓存键枚举"""
    USER_VIP_INFO = "user:vip:info:{user_id}"
    USER_PROFILE = "user:profile:{user_id}:{tenant_id}"
    USER_PERMISSIONS = "user:permissions:{user_id}"


class GameCacheKeyEnum(CacheKeyEnum):
    """游戏相关缓存键枚举"""
    GAME_CONFIG = "game:config:{game_id}"
    GAME_STATS = "game:stats:{game_id}:{user_id}"


# 示例1: 基本的内存TTL缓存
@u_l_cache(ttl_seconds=60)
def get_user_name(user_id: int) -> str:
    """获取用户名（同步函数示例）"""
    print(f"正在从数据库查询用户 {user_id}...")
    # 模拟数据库查询延迟
    time.sleep(0.1)
    return f"用户_{user_id}"


# 示例2: 异步函数的内存TTL缓存
@u_l_cache(ttl_seconds=300)
async def fetch_user_data(user_id: int) -> Dict[str, Any]:
    """获取用户数据（异步函数示例）"""
    print(f"正在从数据库获取用户 {user_id} 的数据...")
    await asyncio.sleep(0.5)  # 模拟数据库查询延迟
    return {
        "user_id": user_id,
        "name": f"User_{user_id}",
        "email": f"user{user_id}@example.com",
        "created_at": "2024-01-01T00:00:00Z"
    }


# 示例3: Redis存储的缓存
@u_l_cache(storage_type=StorageType.REDIS, ttl_seconds=3600)
async def get_shared_data() -> Dict[str, Any]:
    """获取共享数据（Redis存储示例）"""
    print("正在从外部API获取共享数据...")
    await asyncio.sleep(1)  # 模拟API调用延迟
    return {
        "data": "some shared data",
        "timestamp": time.time(),
        "source": "external_api"
    }


# 示例4: LRU缓存策略
@u_l_cache(
    cache_type=CacheType.LRU,
    max_size=100,
    storage_type=StorageType.MEMORY
)
def calculate_fibonacci(n: int) -> int:
    """计算斐波那契数列（LRU缓存示例）"""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)


# 示例5: 自定义缓存键生成
def make_user_key(user_id: int, tenant_id: str) -> str:
    """自定义缓存键生成函数"""
    return f"custom_user:{tenant_id}:{user_id}"


@u_l_cache(key_func=make_user_key, ttl_seconds=1800)
def get_user_permissions(user_id: int, tenant_id: str) -> List[str]:
    """获取用户权限（自定义键生成示例）"""
    print(f"正在查询用户 {user_id} 在租户 {tenant_id} 的权限...")
    time.sleep(0.2)
    return ["read", "write", "delete"]


# 示例6: 使用key_params自动生成缓存键
@u_l_cache(key_params=['user_id', 'tenant_id'], ttl_seconds=1200)
def get_document(doc_id: int, user_id: int, tenant_id: str) -> Dict[str, Any]:
    """获取文档（自动键生成示例）"""
    print(f"正在获取文档 {doc_id}...")
    time.sleep(0.3)
    return {
        "doc_id": doc_id,
        "content": f"Document content for {doc_id}",
        "owner": user_id,
        "tenant": tenant_id
    }


# 示例7: 用户级别版本控制缓存
@u_l_cache(
    cache_key_enum=UserCacheKeyEnum.USER_VIP_INFO,
    key_params=["user_id"],
    make_expire_sec_func=lambda result: 3600 if result.get("is_vip") else 1800
)
async def get_user_vip_info(user_id: int) -> Dict[str, Any]:
    """获取用户VIP信息（用户级别版本控制示例）"""
    print(f"正在获取用户 {user_id} 的VIP信息...")
    await asyncio.sleep(0.8)

    is_vip = user_id % 3 == 0  # 模拟VIP判断逻辑
    return {
        "user_id": user_id,
        "is_vip": is_vip,
        "vip_level": "gold" if is_vip else "none",
        "expires_at": "2024-12-31T23:59:59Z" if is_vip else None
    }


# 示例8: 多参数缓存键
@u_l_cache(
    cache_key_enum=UserCacheKeyEnum.USER_PROFILE,
    key_params=["user_id", "tenant_id"],
    storage_type=StorageType.REDIS
)
async def get_user_profile(user_id: int, tenant_id: str) -> Dict[str, Any]:
    """获取用户资料（多参数缓存键示例）"""
    print(f"正在获取用户 {user_id} 在租户 {tenant_id} 的资料...")
    await asyncio.sleep(0.6)
    return {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "name": f"User_{user_id}",
        "avatar": f"https://example.com/avatars/{user_id}.jpg",
        "settings": {"theme": "dark", "language": "zh-CN"}
    }


# 示例9: 缓存预加载
def user_ids_provider():
    """用户ID提供者，用于缓存预加载"""
    # 这些ID可以是来自配置、数据库或其他来源
    for user_id in [1, 2, 3, 4, 5]:
        yield (user_id,), {}  # (args, kwargs)


@u_l_cache(storage_type='memory', preload_provider=user_ids_provider)
def get_user_name_preload(user_id: int) -> str:
    """获取用户名（预加载示例）"""
    print(f"从数据库查询用户 {user_id}...")
    return f"用户_{user_id}"


# 示例10: 直接使用缓存管理器
class UserCacheService:
    """用户缓存服务示例"""
    
    def __init__(self):
        config = CacheConfig(
            storage_type=StorageType.REDIS,
            prefix="user_cache:"
        )
        self.cache = UniversalCacheManager(config)
    
    async def get_user_data(self, user_id: int) -> Dict[str, Any]:
        """获取用户数据"""
        cache_key = f"user_data:{user_id}"
        
        # 使用用户级别版本控制
        cached_data = await self.cache.get(cache_key, user_id=str(user_id))
        if cached_data:
            return cached_data
        
        # 缓存未命中，获取数据
        user_data = await self._fetch_user_data(user_id)
        
        # 存储到缓存，使用用户级别版本控制
        await self.cache.set(cache_key, user_data, user_id=str(user_id))
        return user_data
    
    async def invalidate_user_cache(self, user_id: int):
        """使用户的所有缓存失效"""
        await self.cache.invalidate_user_cache(str(user_id))
    
    async def _fetch_user_data(self, user_id: int) -> Dict[str, Any]:
        """模拟从数据库获取用户数据"""
        await asyncio.sleep(0.5)
        return {
            "user_id": user_id,
            "name": f"User_{user_id}",
            "email": f"user{user_id}@example.com",
            "created_at": "2024-01-01T00:00:00Z"
        }


async def run_examples():
    """运行所有示例"""
    print("=== L-Cache 使用示例 ===\n")
    
    # 示例1: 基本内存TTL缓存
    print("1. 基本内存TTL缓存:")
    print(get_user_name(123))  # 第一次调用，会执行函数
    print(get_user_name(123))  # 第二次调用，从缓存返回
    print()
    
    # 示例2: 异步函数缓存
    print("2. 异步函数缓存:")
    result1 = await fetch_user_data(456)
    print(f"第一次调用: {result1}")
    result2 = await fetch_user_data(456)
    print(f"第二次调用: {result2}")
    print()
    
    # 示例3: Redis存储（需要Redis服务）
    print("3. Redis存储缓存:")
    try:
        shared_data1 = await get_shared_data()
        print(f"第一次调用: {shared_data1}")
        shared_data2 = await get_shared_data()
        print(f"第二次调用: {shared_data2}")
    except Exception as e:
        print(f"Redis连接失败: {e}")
    print()
    
    # 示例4: LRU缓存
    print("4. LRU缓存:")
    print(f"斐波那契(10): {calculate_fibonacci(10)}")
    print(f"斐波那契(10): {calculate_fibonacci(10)}")  # 从缓存返回
    print()
    
    # 示例5: 自定义缓存键
    print("5. 自定义缓存键:")
    perms1 = get_user_permissions(789, "tenant_a")
    print(f"权限1: {perms1}")
    perms2 = get_user_permissions(789, "tenant_a")
    print(f"权限2: {perms2}")
    print()
    
    # 示例6: 自动键生成
    print("6. 自动键生成:")
    doc1 = get_document(1, 123, "tenant_b")
    print(f"文档1: {doc1}")
    doc2 = get_document(1, 123, "tenant_b")
    print(f"文档2: {doc2}")
    print()
    
    # 示例7: 用户级别版本控制
    print("7. 用户级别版本控制:")
    vip1 = await get_user_vip_info(123)
    print(f"VIP信息1: {vip1}")
    vip2 = await get_user_vip_info(123)
    print(f"VIP信息2: {vip2}")
    print()
    
    # 示例8: 多参数缓存键
    print("8. 多参数缓存键:")
    profile1 = await get_user_profile(456, "tenant_c")
    print(f"资料1: {profile1}")
    profile2 = await get_user_profile(456, "tenant_c")
    print(f"资料2: {profile2}")
    print()
    
    # 示例9: 缓存预加载
    print("9. 缓存预加载:")
    await preload_all_caches()
    print(f"预加载后调用: {get_user_name_preload(1)}")
    print(f"预加载后调用: {get_user_name_preload(2)}")
    print()
    
    # 示例10: 直接使用缓存管理器
    print("10. 直接使用缓存管理器:")
    cache_service = UserCacheService()
    user_data1 = await cache_service.get_user_data(999)
    print(f"用户数据1: {user_data1}")
    user_data2 = await cache_service.get_user_data(999)
    print(f"用户数据2: {user_data2}")
    
    # 演示缓存失效
    await cache_service.invalidate_user_cache(999)
    user_data3 = await cache_service.get_user_data(999)
    print(f"失效后重新获取: {user_data3}")
    print()
    
    # 全局缓存控制
    print("11. 全局缓存控制:")
    await invalidate_all_caches()
    print("所有缓存已失效")
    
    await invalidate_user_cache("123")
    print("用户123的缓存已失效")


if __name__ == "__main__":
    asyncio.run(run_examples()) 