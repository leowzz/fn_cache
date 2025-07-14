# 基础示例

本文档提供了 fn_cache 的基础使用示例，帮助您快速上手。

## 🚀 快速开始

### 1. 基本缓存

最简单的缓存使用方式：

```python
from fn_cache import cached
import time

@cached(ttl_seconds=60)  # 缓存60秒
def get_user_info(user_id: int):
    print(f"正在查询用户 {user_id} 的信息...")
    time.sleep(1)  # 模拟数据库查询
    return {
        "user_id": user_id,
        "name": f"用户_{user_id}",
        "email": f"user{user_id}@example.com"
    }

# 第一次调用 - 执行函数并缓存结果
result1 = get_user_info(123)
print(f"结果: {result1}")

# 第二次调用 - 直接从缓存返回
result2 = get_user_info(123)
print(f"结果: {result2}")  # 相同结果，但不会打印查询信息
```

**输出：**
```
正在查询用户 123 的信息...
结果: {'user_id': 123, 'name': '用户_123', 'email': 'user123@example.com'}
结果: {'user_id': 123, 'name': '用户_123', 'email': 'user123@example.com'}
```

### 2. 异步函数缓存

fn_cache 完美支持异步函数：

```python
import asyncio
from fn_cache import cached

@cached(ttl_seconds=300)  # 缓存5分钟
async def fetch_user_data(user_id: int):
    print(f"正在异步获取用户 {user_id} 的数据...")
    await asyncio.sleep(1)  # 模拟异步数据库查询
    return {
        "user_id": user_id,
        "profile": f"用户_{user_id} 的详细资料",
        "last_login": "2024-01-01 10:00:00"
    }

async def main():
    # 第一次调用
    result1 = await fetch_user_data(456)
    print(f"结果: {result1}")
    
    # 第二次调用 - 命中缓存
    result2 = await fetch_user_data(456)
    print(f"结果: {result2}")

# 运行异步函数
asyncio.run(main())
```

## 🎛️ 缓存策略示例

### TTL 缓存（基于时间过期）

```python
from fn_cache import cached, CacheType
import time

@cached(
    cache_type=CacheType.TTL,
    ttl_seconds=30  # 30秒后过期
)
def get_temporary_data(key: str):
    print(f"获取临时数据: {key}")
    return f"临时数据_{key}"

# 第一次调用
result1 = get_temporary_data("test")
print(f"结果: {result1}")

# 30秒内再次调用 - 命中缓存
result2 = get_temporary_data("test")
print(f"结果: {result2}")

# 等待31秒后调用 - 缓存过期，重新执行
time.sleep(31)
result3 = get_temporary_data("test")
print(f"结果: {result3}")
```

### LRU 缓存（最近最少使用）

```python
from fn_cache import cached, CacheType

@cached(
    cache_type=CacheType.LRU,
    max_size=3  # 最多缓存3个条目
)
def get_cached_data(key: str):
    print(f"获取数据: {key}")
    return f"数据_{key}"

# 添加4个不同的键
for i in range(4):
    result = get_cached_data(f"key_{i}")
    print(f"结果: {result}")

# 再次获取第一个键 - 由于LRU淘汰，需要重新获取
result = get_cached_data("key_0")
print(f"结果: {result}")
```

## 💾 存储后端示例

### 内存存储（默认）

```python
from fn_cache import cached, StorageType

@cached(
    storage_type=StorageType.MEMORY,
    ttl_seconds=300
)
def get_memory_cached_data(key: str):
    print(f"获取内存缓存数据: {key}")
    return f"内存缓存数据_{key}"

# 使用内存缓存
result1 = get_memory_cached_data("test")
result2 = get_memory_cached_data("test")  # 命中缓存
```

### Redis 存储

```python
from fn_cache import cached, StorageType, SerializerType

@cached(
    storage_type=StorageType.REDIS,
    serializer_type=SerializerType.JSON,
    ttl_seconds=3600,  # 1小时
    prefix="myapp:"  # 自定义前缀
)
def get_redis_cached_data(key: str):
    print(f"获取Redis缓存数据: {key}")
    return {
        "key": key,
        "value": f"Redis缓存数据_{key}",
        "timestamp": "2024-01-01 12:00:00"
    }

# 使用Redis缓存
result1 = get_redis_cached_data("test")
result2 = get_redis_cached_data("test")  # 命中缓存
```

## 🔑 缓存键示例

### 默认缓存键

```python
@cached(ttl_seconds=300)
def get_user_info(user_id: int, include_profile: bool = True):
    print(f"查询用户 {user_id}，包含资料: {include_profile}")
    return {
        "user_id": user_id,
        "profile": include_profile
    }

# 不同的参数组合会生成不同的缓存键
result1 = get_user_info(123, True)   # 缓存键: fn_cache:get_user_info:123:True
result2 = get_user_info(123, False)  # 缓存键: fn_cache:get_user_info:123:False
result3 = get_user_info(123, True)   # 命中第一个缓存
```

### 自定义缓存键

```python
@cached(
    ttl_seconds=300,
    key_func=lambda *args, **kwargs: f"user:{args[0]}:{kwargs.get('version', 'v1')}"
)
def get_user_data(user_id: int, version: str = "v1"):
    print(f"获取用户 {user_id} 数据，版本: {version}")
    return {"user_id": user_id, "version": version}

# 使用自定义缓存键
result1 = get_user_data(123, "v1")  # 缓存键: user:123:v1
result2 = get_user_data(123, "v2")  # 缓存键: user:123:v2
result3 = get_user_data(123, "v1")  # 命中第一个缓存
```

### 使用缓存键枚举

```python
from fn_cache import CacheKeyEnum

class UserCacheKeys(CacheKeyEnum):
    USER_PROFILE = "user:{user_id}:profile"
    USER_SETTINGS = "user:{user_id}:settings:{setting_type}"

@cached(
    ttl_seconds=300,
    key_func=lambda *args, **kwargs: UserCacheKeys.USER_PROFILE.format(user_id=args[0])
)
def get_user_profile(user_id: int):
    print(f"获取用户 {user_id} 的资料")
    return {"user_id": user_id, "profile": "用户资料"}

@cached(
    ttl_seconds=300,
    key_func=lambda *args, **kwargs: UserCacheKeys.USER_SETTINGS.format(
        user_id=args[0], 
        setting_type=args[1]
    )
)
def get_user_settings(user_id: int, setting_type: str):
    print(f"获取用户 {user_id} 的 {setting_type} 设置")
    return {"user_id": user_id, "setting_type": setting_type, "settings": {}}
```

## 📊 序列化示例

### JSON 序列化（默认）

```python
from fn_cache import cached, SerializerType

@cached(
    serializer_type=SerializerType.JSON,
    ttl_seconds=300
)
def get_json_data(key: str):
    return {
        "key": key,
        "value": f"值_{key}",
        "numbers": [1, 2, 3, 4, 5],
        "nested": {"a": 1, "b": 2}
    }

result = get_json_data("test")
```

### Pickle 序列化

```python
from dataclasses import dataclass
from fn_cache import cached, SerializerType

@dataclass
class UserProfile:
    user_id: int
    name: str
    email: str

@cached(
    serializer_type=SerializerType.PICKLE,
    ttl_seconds=300
)
def get_complex_data(user_id: int):
    return UserProfile(
        user_id=user_id,
        name=f"用户_{user_id}",
        email=f"user{user_id}@example.com"
    )

result = get_complex_data(123)
print(f"用户: {result.name}, 邮箱: {result.email}")
```

### MessagePack 序列化

```python
from fn_cache import cached, SerializerType

@cached(
    serializer_type=SerializerType.MESSAGEPACK,
    ttl_seconds=300
)
def get_efficient_data(key: str):
    return {
        "key": key,
        "data": [i for i in range(1000)],  # 大数据量
        "metadata": {"created": "2024-01-01", "version": "1.0"}
    }

result = get_efficient_data("large_data")
```

## 🎛️ 全局控制示例

### 全局缓存开关

```python
from fn_cache import (
    cached, 
    enable_global_cache, 
    disable_global_cache,
    is_global_cache_enabled
)

@cached(ttl_seconds=60)
def controlled_function(x: int):
    print(f"执行函数: {x}")
    return x * 2

# 正常使用缓存
print("=== 正常模式 ===")
print(controlled_function(5))  # 执行并缓存
print(controlled_function(5))  # 命中缓存

# 禁用全局缓存
print("\n=== 禁用缓存 ===")
disable_global_cache()
print(f"缓存已禁用: {is_global_cache_enabled()}")

print(controlled_function(5))  # 再次执行（缓存被禁用）

# 重新启用缓存
print("\n=== 重新启用缓存 ===")
enable_global_cache()
print(f"缓存已启用: {is_global_cache_enabled()}")

print(controlled_function(5))  # 命中缓存
```

### 缓存失效

```python
from fn_cache import cached, invalidate_all_caches

@cached(ttl_seconds=3600)  # 1小时缓存
def get_config_data():
    print("获取配置数据...")
    return {"version": "1.0", "settings": {"debug": True}}

# 第一次调用
result1 = get_config_data()

# 第二次调用 - 命中缓存
result2 = get_config_data()

# 使所有缓存失效
await invalidate_all_caches()

# 第三次调用 - 缓存已失效，重新执行
result3 = get_config_data()
```

## 📈 监控示例

### 缓存统计

```python
from fn_cache import cached, get_cache_statistics

@cached(ttl_seconds=60)
def monitored_function(x: int):
    return x * x

# 调用函数几次
for i in range(10):
    monitored_function(i)

# 获取缓存统计信息
stats = get_cache_statistics()
print("缓存统计:")
for cache_id, cache_stats in stats.items():
    print(f"  {cache_id}:")
    print(f"    命中率: {cache_stats['hit_rate']:.2%}")
    print(f"    总调用次数: {cache_stats['total_calls']}")
    print(f"    缓存命中次数: {cache_stats['hits']}")
    print(f"    缓存未命中次数: {cache_stats['misses']}")
    print(f"    平均响应时间: {cache_stats['avg_response_time']:.4f}s")
```

### 内存监控

```python
from fn_cache import (
    cached, 
    start_cache_memory_monitoring,
    get_cache_memory_usage,
    get_cache_memory_summary
)

# 启动内存监控（每5分钟报告一次）
start_cache_memory_monitoring(interval_seconds=300)

@cached(ttl_seconds=300)
def memory_monitored_function(x: int):
    return x * x

# 调用函数几次
for i in range(100):
    memory_monitored_function(i)

# 获取内存使用情况
memory_usage = get_cache_memory_usage()
print("内存使用情况:")
for info in memory_usage:
    print(f"  管理器: {info.manager_id}")
    print(f"  存储类型: {info.storage_type}")
    print(f"  缓存类型: {info.cache_type}")
    print(f"  条目数量: {info.item_count}")
    print(f"  内存占用: {info.memory_mb:.2f} MB")
    print(f"  最大容量: {info.max_size}")

# 获取内存使用摘要
summary = get_cache_memory_summary()
print(f"\n内存使用摘要:")
print(f"  总条目数: {summary['total_items']}")
print(f"  总内存占用: {summary['total_memory_mb']:.2f} MB")
print(f"  平均每个条目: {summary['avg_memory_per_item_mb']:.4f} MB")
```

## 🔧 高级示例

### 动态过期时间

```python
def dynamic_ttl(result):
    """根据结果动态计算过期时间"""
    if result.get("is_vip"):
        return 3600  # VIP用户缓存1小时
    else:
        return 300   # 普通用户缓存5分钟

@cached(
    ttl_seconds=300,
    make_expire_sec_func=dynamic_ttl
)
def get_user_info(user_id: int):
    is_vip = user_id % 3 == 0  # 模拟VIP判断
    return {"user_id": user_id, "is_vip": is_vip}

# 测试不同用户
for user_id in [1, 2, 3, 4, 5, 6]:
    result = get_user_info(user_id)
    print(f"用户 {user_id}: VIP={result['is_vip']}")
```

### 缓存预热

```python
def user_ids_provider():
    """提供需要预加载的用户ID"""
    return [(user_id,) for user_id in [1, 2, 3, 4, 5]]

@cached(
    ttl_seconds=3600,
    preload_provider=user_ids_provider
)
def get_user_name(user_id: int):
    print(f"从数据库查询用户 {user_id}...")
    return f"用户_{user_id}"

# 在应用启动时预加载
async def startup():
    from fn_cache import preload_all_caches
    print("开始预加载缓存...")
    await preload_all_caches()
    print("缓存预加载完成")

# 预加载后，数据已在缓存中
async def main():
    await startup()
    
    # 此时调用函数不会执行数据库查询
    for user_id in [1, 2, 3, 4, 5]:
        name = get_user_name(user_id)
        print(f"用户 {user_id}: {name}")

asyncio.run(main())
```

## 📝 完整示例

```python
import asyncio
import time
from fn_cache import (
    cached, 
    CacheType, 
    StorageType, 
    SerializerType,
    get_cache_statistics,
    start_cache_memory_monitoring
)

# 启动监控
start_cache_memory_monitoring(interval_seconds=60)

# 1. 基本TTL缓存
@cached(ttl_seconds=30)
def get_user_profile(user_id: int):
    print(f"查询用户资料: {user_id}")
    time.sleep(0.5)
    return {"user_id": user_id, "name": f"用户_{user_id}"}

# 2. LRU缓存
@cached(cache_type=CacheType.LRU, max_size=10)
def get_product_info(product_id: str):
    print(f"查询商品信息: {product_id}")
    return {"product_id": product_id, "name": f"商品_{product_id}"}

# 3. 异步函数缓存
@cached(ttl_seconds=60)
async def fetch_orders(user_id: int):
    print(f"异步获取订单: {user_id}")
    await asyncio.sleep(0.3)
    return [{"order_id": f"order_{user_id}_{i}"} for i in range(3)]

# 4. 自定义缓存键
@cached(
    ttl_seconds=120,
    key_func=lambda *args, **kwargs: f"custom:{args[0]}:{kwargs.get('lang', 'zh')}"
)
def get_localized_content(content_id: str, lang: str = "zh"):
    print(f"获取本地化内容: {content_id} ({lang})")
    return f"内容_{content_id}_{lang}"

async def main():
    print("=== fn_cache 基础示例 ===\n")
    
    # 测试基本缓存
    print("1. 测试基本TTL缓存:")
    print(get_user_profile(1))  # 执行
    print(get_user_profile(1))  # 命中缓存
    print()
    
    # 测试LRU缓存
    print("2. 测试LRU缓存:")
    for i in range(5):
        get_product_info(f"prod_{i}")
    print()
    
    # 测试异步缓存
    print("3. 测试异步缓存:")
    orders1 = await fetch_orders(100)
    orders2 = await fetch_orders(100)  # 命中缓存
    print(f"订单数量: {len(orders1)}")
    print()
    
    # 测试自定义缓存键
    print("4. 测试自定义缓存键:")
    print(get_localized_content("welcome", "zh"))
    print(get_localized_content("welcome", "en"))
    print(get_localized_content("welcome", "zh"))  # 命中缓存
    print()
    
    # 显示统计信息
    print("5. 缓存统计:")
    stats = get_cache_statistics()
    for cache_id, cache_stats in stats.items():
        print(f"  {cache_id}: 命中率 {cache_stats['hit_rate']:.1%}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🎯 下一步

完成基础示例后，建议您：

1. **探索进阶功能**：
   - [进阶示例](advanced.md) - 更复杂的使用场景
   - [全局开关示例](global_switch.md) - 全局缓存控制
   - [内存监控示例](memory_monitoring.md) - 监控功能

2. **了解核心概念**：
   - [缓存装饰器](../concepts/decorators.md) - 详细概念说明
   - [缓存管理器](../concepts/manager.md) - 底层管理
   - [存储后端](../concepts/storages.md) - 存储配置

3. **查看API文档**：
   - [装饰器API](../api/decorators.md) - 完整API参考
   - [管理器API](../api/manager.md) - 管理器API 