#!/usr/bin/env python3
"""
Leo Cache 简化版综合功能演示示例

本示例展示了 Leo Cache 库的核心功能，仅使用内存存储：
- 多种序列化类型（JSON、Pickle、MessagePack）
- 装饰器模式使用
- 内存监控和统计功能
- 缓存预热和批量操作
- 动态过期时间
- 全局缓存开关
- 自定义缓存键生成

运行方式：
    python examples/simple_comprehensive_example.py
"""

import asyncio
import time
import random
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass

# 导入 Leo Cache 核心组件
from fn_cache import (
    # 核心管理器和存储
    UniversalCacheManager,
    
    # 配置和枚举
    CacheConfig,
    CacheType,
    StorageType,
    SerializerType,
    CacheKeyEnum,
    
    # 装饰器
    cached,
    invalidate_all_caches,
    
    # 内存监控
    start_cache_memory_monitoring,
    stop_cache_memory_monitoring,
    get_cache_memory_usage,
    get_cache_memory_summary,
    register_cache_manager_for_monitoring,
    
    # 缓存统计
    get_cache_statistics,
    reset_cache_statistics,
    
    # 全局开关
    enable_global_cache,
    disable_global_cache,
    is_global_cache_enabled,
)


# ============================================================================
# 数据模型定义
# ============================================================================

@dataclass
class UserProfile:
    """用户资料数据模型"""
    user_id: int
    username: str
    email: str
    avatar_url: str
    created_at: datetime
    preferences: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'avatar_url': self.avatar_url,
            'created_at': self.created_at.isoformat(),
            'preferences': self.preferences
        }


@dataclass
class Product:
    """商品数据模型"""
    product_id: str
    name: str
    price: float
    category: str
    tags: List[str]
    stock: int
    metadata: Dict[str, Any]


# ============================================================================
# 自定义缓存键定义
# ============================================================================

class BusinessCacheKeys:
    """业务缓存键定义"""
    USER_PROFILE = "user:{user_id}:profile"
    USER_PREFERENCES = "user:{user_id}:preferences"
    PRODUCT_INFO = "product:{product_id}:info"
    PRODUCT_LIST = "product:category:{category}:list"
    HOT_PRODUCTS = "product:hot:list"
    USER_ORDERS = "user:{user_id}:orders"
    SYSTEM_CONFIG = "system:config:{config_key}"
    
    @classmethod
    def format(cls, key: str, **kwargs) -> str:
        """格式化缓存键，替换模板中的参数"""
        return key.format(**kwargs)


# ============================================================================
# 模拟业务服务类
# ============================================================================

class UserService:
    """用户服务类 - 演示不同序列化类型的使用"""
    
    def __init__(self):
        # 创建不同配置的缓存管理器
        self._setup_cache_managers()
    
    def _setup_cache_managers(self):
        """设置不同配置的缓存管理器"""
        
        # 1. 内存存储 + JSON序列化 - 适合简单数据
        self.json_cache = UniversalCacheManager(
            config=CacheConfig(
                storage_type=StorageType.MEMORY,
                serializer_type=SerializerType.JSON,
                ttl_seconds=300,  # 5分钟
                enable_statistics=True,
                enable_memory_monitoring=True
            )
        )
        
        # 2. 内存存储 + Pickle序列化 - 适合复杂对象
        self.pickle_cache = UniversalCacheManager(
            config=CacheConfig(
                storage_type=StorageType.MEMORY,
                serializer_type=SerializerType.PICKLE,
                ttl_seconds=1800,  # 30分钟
                enable_statistics=True,
                enable_memory_monitoring=True
            )
        )
        
        # 3. 内存存储 + MessagePack序列化 - 适合大数据量
        self.msgpack_cache = UniversalCacheManager(
            config=CacheConfig(
                storage_type=StorageType.MEMORY,
                serializer_type=SerializerType.MESSAGEPACK,
                ttl_seconds=3600,  # 1小时
                enable_statistics=True,
                enable_memory_monitoring=True
            )
        )
        
        # 注册缓存管理器用于监控
        register_cache_manager_for_monitoring(self.json_cache)
        register_cache_manager_for_monitoring(self.pickle_cache)
        register_cache_manager_for_monitoring(self.msgpack_cache)
    
    async def get_user_profile_json(self, user_id: int) -> Dict[str, Any]:
        """获取用户资料 - 使用JSON序列化"""
        cache_key = BusinessCacheKeys.format(BusinessCacheKeys.USER_PROFILE, user_id=user_id)
        
        # 尝试从缓存获取
        cached_data = await self.json_cache.get(cache_key)
        if cached_data:
            print(f"✅ 从JSON缓存获取用户资料: {user_id}")
            return cached_data
        
        # 模拟数据库查询
        print(f"🔄 从数据库查询用户资料: {user_id}")
        await asyncio.sleep(0.1)  # 模拟网络延迟
        
        # 创建用户资料
        user_profile = {
            'user_id': user_id,
            'username': f'user_{user_id}',
            'email': f'user_{user_id}@example.com',
            'avatar_url': f'https://avatars.com/{user_id}.jpg',
            'created_at': datetime.now().isoformat(),
            'preferences': {
                'theme': 'dark',
                'language': 'zh-CN',
                'notifications': True
            }
        }
        
        # 存储到缓存
        await self.json_cache.set(cache_key, user_profile, ttl_seconds=300)
        return user_profile
    
    async def get_user_profile_pickle(self, user_id: int) -> UserProfile:
        """获取用户资料对象 - 使用Pickle序列化"""
        cache_key = BusinessCacheKeys.format(BusinessCacheKeys.USER_PROFILE, user_id=user_id)
        
        # 尝试从缓存获取
        cached_profile = await self.pickle_cache.get(cache_key)
        if cached_profile:
            print(f"✅ 从Pickle缓存获取用户资料对象: {user_id}")
            return cached_profile
        
        # 模拟数据库查询
        print(f"🔄 从数据库查询用户资料对象: {user_id}")
        await asyncio.sleep(0.1)
        
        # 创建用户资料对象
        user_profile = UserProfile(
            user_id=user_id,
            username=f'user_{user_id}',
            email=f'user_{user_id}@example.com',
            avatar_url=f'https://avatars.com/{user_id}.jpg',
            created_at=datetime.now(),
            preferences={
                'theme': 'dark',
                'language': 'zh-CN',
                'notifications': True
            }
        )
        
        # 存储到缓存
        await self.pickle_cache.set(cache_key, user_profile, ttl_seconds=1800)
        return user_profile
    
    async def get_user_orders_msgpack(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户订单列表 - 使用MessagePack序列化"""
        cache_key = BusinessCacheKeys.format(BusinessCacheKeys.USER_ORDERS, user_id=user_id)
        
        # 尝试从缓存获取
        cached_orders = await self.msgpack_cache.get(cache_key)
        if cached_orders:
            print(f"✅ 从MessagePack缓存获取用户订单: {user_id}")
            return cached_orders
        
        # 模拟数据库查询
        print(f"🔄 从数据库查询用户订单: {user_id}")
        await asyncio.sleep(0.2)
        
        # 创建订单数据
        orders = [
            {
                'order_id': f'ORD_{user_id}_{i}',
                'product_id': f'PROD_{random.randint(1000, 9999)}',
                'quantity': random.randint(1, 5),
                'total_price': round(random.uniform(10.0, 1000.0), 2),
                'status': random.choice(['pending', 'shipped', 'delivered']),
                'created_at': datetime.now().isoformat(),
                'items': [
                    {
                        'product_name': f'Product {j}',
                        'price': round(random.uniform(5.0, 200.0), 2),
                        'quantity': random.randint(1, 3)
                    }
                    for j in range(random.randint(1, 4))
                ]
            }
            for i in range(random.randint(3, 8))
        ]
        
        # 存储到缓存
        await self.msgpack_cache.set(cache_key, orders, ttl_seconds=3600)
        return orders


class ProductService:
    """商品服务类 - 演示装饰器模式"""
    
    def __init__(self):
        # 创建商品专用的缓存管理器
        self.cache_manager = UniversalCacheManager(
            config=CacheConfig(
                storage_type=StorageType.MEMORY,
                serializer_type=SerializerType.JSON,
                ttl_seconds=1800,
                enable_statistics=True,
                enable_memory_monitoring=True
            )
        )
        register_cache_manager_for_monitoring(self.cache_manager)
    
    @cached(ttl_seconds=600, storage_type=StorageType.MEMORY)
    async def get_product_info(self, product_id: str) -> Dict[str, Any]:
        """获取商品信息 - 使用装饰器缓存"""
        print(f"🔄 从数据库查询商品信息: {product_id}")
        await asyncio.sleep(0.1)
        
        return {
            'product_id': product_id,
            'name': f'Product {product_id}',
            'price': round(random.uniform(10.0, 500.0), 2),
            'category': random.choice(['electronics', 'clothing', 'books', 'home']),
            'tags': random.sample(['new', 'popular', 'discount', 'premium'], 2),
            'stock': random.randint(0, 100),
            'metadata': {
                'brand': f'Brand {random.randint(1, 10)}',
                'rating': round(random.uniform(3.0, 5.0), 1),
                'reviews_count': random.randint(10, 1000)
            }
        }
    
    @cached(ttl_seconds=1200, storage_type=StorageType.MEMORY)
    async def get_products_by_category(self, category: str, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """获取分类商品列表 - 使用内存缓存"""
        print(f"🔄 从数据库查询分类商品: {category}, 页码: {page}")
        await asyncio.sleep(0.2)
        
        # 模拟分页数据
        total_products = random.randint(50, 200)
        start_idx = (page - 1) * limit
        end_idx = min(start_idx + limit, total_products)
        
        products = [
            {
                'product_id': f'PROD_{category}_{i}',
                'name': f'{category.title()} Product {i}',
                'price': round(random.uniform(5.0, 300.0), 2),
                'category': category,
                'stock': random.randint(0, 50)
            }
            for i in range(start_idx + 1, end_idx + 1)
        ]
        
        return {
            'products': products,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_products,
                'total_pages': (total_products + limit - 1) // limit
            }
        }
    
    @cached(
        ttl_seconds=1800,
        storage_type=StorageType.MEMORY,
        key_func=lambda *args, **kwargs: f"hot_products:{datetime.now().strftime('%Y%m%d')}"
    )
    async def get_hot_products(self) -> List[Dict[str, Any]]:
        """获取热门商品 - 使用自定义缓存键"""
        print("🔄 从数据库查询热门商品")
        await asyncio.sleep(0.3)
        
        return [
            {
                'product_id': f'HOT_{i}',
                'name': f'Hot Product {i}',
                'price': round(random.uniform(20.0, 200.0), 2),
                'category': random.choice(['electronics', 'clothing', 'books']),
                'sales_count': random.randint(100, 10000),
                'rating': round(random.uniform(4.0, 5.0), 1)
            }
            for i in range(1, 11)
        ]


# ============================================================================
# 动态过期时间函数
# ============================================================================

def dynamic_ttl_for_user_data(user_data: Dict[str, Any]) -> int:
    """根据用户数据动态计算过期时间"""
    # VIP用户缓存时间更长
    if user_data.get('vip_level', 0) > 0:
        return 3600  # 1小时
    # 活跃用户缓存时间中等
    elif user_data.get('last_login_days', 30) < 7:
        return 1800  # 30分钟
    # 普通用户缓存时间较短
    else:
        return 600  # 10分钟


# ============================================================================
# 缓存预热和批量操作
# ============================================================================

async def warm_up_cache():
    """缓存预热函数"""
    print("\n🔥 开始缓存预热...")
    
    user_service = UserService()
    product_service = ProductService()
    
    # 预热用户数据
    user_ids = [1, 2, 3, 4, 5]
    for user_id in user_ids:
        await user_service.get_user_profile_json(user_id)
        await user_service.get_user_profile_pickle(user_id)
        await user_service.get_user_orders_msgpack(user_id)
    
    # 预热商品数据
    product_ids = ['PROD_001', 'PROD_002', 'PROD_003']
    for product_id in product_ids:
        await product_service.get_product_info(product_id)
    
    # 预热分类商品
    categories = ['electronics', 'clothing', 'books']
    for category in categories:
        await product_service.get_products_by_category(category, 1, 10)
    
    # 预热热门商品
    await product_service.get_hot_products()
    
    print("✅ 缓存预热完成")


# ============================================================================
# 性能测试函数
# ============================================================================

async def performance_test():
    """性能测试函数"""
    print("\n⚡ 开始性能测试...")
    
    user_service = UserService()
    product_service = ProductService()
    
    # 测试缓存命中性能
    start_time = time.time()
    
    # 第一次调用（缓存未命中）
    for i in range(5):
        await user_service.get_user_profile_json(i + 1)
        await product_service.get_product_info(f'PROD_{i+1:03d}')
    
    first_call_time = time.time() - start_time
    
    # 第二次调用（缓存命中）
    start_time = time.time()
    for i in range(5):
        await user_service.get_user_profile_json(i + 1)
        await product_service.get_product_info(f'PROD_{i+1:03d}')
    
    second_call_time = time.time() - start_time
    
    print(f"📊 性能测试结果:")
    print(f"   首次调用（缓存未命中）: {first_call_time:.3f}秒")
    print(f"   再次调用（缓存命中）: {second_call_time:.3f}秒")
    print(f"   性能提升: {first_call_time / second_call_time:.1f}倍")


# ============================================================================
# 监控和统计演示
# ============================================================================

async def demonstrate_monitoring():
    """演示监控和统计功能"""
    print("\n📊 开始监控演示...")
    
    # 启动内存监控
    start_cache_memory_monitoring(interval_seconds=5)
    print("✅ 内存监控已启动")
    
    # 执行一些操作
    user_service = UserService()
    for i in range(3):
        await user_service.get_user_profile_json(i + 1)
        await asyncio.sleep(1)
    
    # 获取内存使用情况
    memory_usage = get_cache_memory_usage()
    print(f"📈 内存使用情况: {memory_usage}")
    
    # 获取内存使用摘要
    memory_summary = get_cache_memory_summary()
    print(f"📋 内存使用摘要: {memory_summary}")
    
    # 获取缓存统计
    stats = get_cache_statistics()
    print(f"📊 缓存统计: {stats}")
    
    # 停止监控
    stop_cache_memory_monitoring()
    print("✅ 内存监控已停止")


# ============================================================================
# 缓存清除演示
# ============================================================================

async def demonstrate_cache_clear():
    """演示缓存清除功能"""
    print("\n🧹 演示缓存清除功能...")
    
    product_service = ProductService()
    
    # 第一次调用，缓存未命中
    print("   第一次调用 get_product_info...")
    await product_service.get_product_info("PROD_CLEAR_001")
    
    # 第二次调用，缓存命中
    print("   第二次调用 get_product_info（应该命中缓存）...")
    await product_service.get_product_info("PROD_CLEAR_001")
    
    # 清除特定函数的缓存
    print("   清除 get_product_info 函数的缓存...")
    await product_service.get_product_info.cache.clear()
    
    # 第三次调用，缓存未命中（因为已清除）
    print("   第三次调用 get_product_info（应该未命中缓存）...")
    await product_service.get_product_info("PROD_CLEAR_001")
    
    print("   ✅ 缓存清除功能演示完成")


# ============================================================================
# 全局缓存开关演示
# ============================================================================

async def demonstrate_global_switch():
    """演示全局缓存开关功能"""
    print("\n🔧 演示全局缓存开关...")
    
    # 检查当前状态
    print(f"当前全局缓存状态: {'启用' if is_global_cache_enabled() else '禁用'}")
    
    # 禁用全局缓存
    disable_global_cache()
    print("已禁用全局缓存")
    
    # 测试缓存效果
    user_service = UserService()
    start_time = time.time()
    await user_service.get_user_profile_json(999)
    disabled_time = time.time() - start_time
    
    # 启用全局缓存
    enable_global_cache()
    print("已启用全局缓存")
    
    # 再次测试
    start_time = time.time()
    await user_service.get_user_profile_json(999)
    enabled_time = time.time() - start_time
    
    print(f"📊 开关效果对比:")
    print(f"   禁用时耗时: {disabled_time:.3f}秒")
    print(f"   启用时耗时: {enabled_time:.3f}秒")


# ============================================================================
# 主演示函数
# ============================================================================

async def main():
    """主演示函数"""
    print("🚀 Leo Cache 简化版综合功能演示")
    print("=" * 50)
    
    try:
        # 1. 基础功能演示
        print("\n1️⃣ 基础功能演示")
        user_service = UserService()
        product_service = ProductService()
        
        # 测试不同序列化类型
        print("\n📝 测试JSON序列化:")
        profile_json = await user_service.get_user_profile_json(1)
        print(f"   用户资料: {profile_json['username']}")
        
        print("\n📝 测试Pickle序列化:")
        profile_pickle = await user_service.get_user_profile_pickle(1)
        print(f"   用户资料对象: {profile_pickle.username}")
        
        print("\n📝 测试MessagePack序列化:")
        orders = await user_service.get_user_orders_msgpack(1)
        print(f"   订单数量: {len(orders)}")
        
        # 2. 装饰器模式演示
        print("\n2️⃣ 装饰器模式演示")
        product_info = await product_service.get_product_info("PROD_001")
        print(f"   商品信息: {product_info['name']}")
        
        products = await product_service.get_products_by_category("electronics", 1, 5)
        print(f"   电子产品数量: {len(products['products'])}")
        
        hot_products = await product_service.get_hot_products()
        print(f"   热门商品数量: {len(hot_products)}")
        
        # 3. 缓存预热
        await warm_up_cache()
        
        # 4. 性能测试
        await performance_test()
        
        # 5. 监控演示
        await demonstrate_monitoring()
        
        # 6. 全局开关演示
        await demonstrate_global_switch()
        
        # 7. 缓存清除演示
        await demonstrate_cache_clear()
        
        # 8. 缓存失效演示
        print("\n7️⃣ 缓存失效演示")
        
        # 7.1 清除特定函数的缓存
        print("   7.1 清除特定函数的缓存...")
        print("   清除 get_product_info 函数的缓存...")
        await product_service.get_product_info.cache.clear()
        print("   清除 get_products_by_category 函数的缓存...")
        await product_service.get_products_by_category.cache.clear()
        print("   清除 get_hot_products 函数的缓存...")
        await product_service.get_hot_products.cache.clear()
        
        # 7.2 清除所有缓存
        print("   7.2 清除所有缓存...")
        await invalidate_all_caches()
        print("   所有缓存已清除")
        
        # 9. 最终统计
        print("\n9️⃣ 最终统计")
        final_stats = get_cache_statistics()
        print(f"   最终缓存统计: {final_stats}")
        
        print("\n✅ 演示完成！")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行主演示
    asyncio.run(main()) 