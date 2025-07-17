# 快速上手

欢迎使用 fn_cache！本教程将帮助您在 5 分钟内掌握 fn_cache 的基本用法。

## 🎯 学习目标

通过本教程，您将学会：

- 使用 `@cached` 装饰器为函数添加缓存
- 配置不同的缓存策略（TTL/LRU）
- 使用不同的存储后端（内存/Redis）
- 处理异步函数缓存
- 使用缓存统计和监控功能

## 🚀 第一步：基本缓存

让我们从一个简单的例子开始：

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

## 🔄 第二步：异步函数缓存

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
        "last_login": "2025-01-01 10:00:00"
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

## 🎛️ 第三步：配置缓存策略

### TTL 缓存（基于时间过期）

```python
from fn_cache import cached, CacheType

@cached(
    cache_type=CacheType.TTL,
    ttl_seconds=30  # 30秒后过期
)
def get_temporary_data(key: str):
    print(f"获取临时数据: {key}")
    return f"临时数据_{key}"
```

### LRU 缓存（最近最少使用）

```python
@cached(
    cache_type=CacheType.LRU,
    max_size=100  # 最多缓存100个条目
)
def get_cached_data(key: str):
    print(f"获取数据: {key}")
    return f"数据_{key}"
```

## 💾 第四步：使用 Redis 存储

如果您有 Redis 服务器，可以切换到 Redis 存储：

```python
from fn_cache import cached, StorageType, SerializerType

@cached(
    storage_type=StorageType.REDIS,
    serializer_type=SerializerType.JSON,
    ttl_seconds=3600  # 1小时
)
def get_shared_data(data_id: str):
    print(f"获取共享数据: {data_id}")
    return {
        "id": data_id,
        "content": f"共享内容_{data_id}",
        "timestamp": "2025-01-01 12:00:00"
    }
```

**注意：** 使用 Redis 存储需要配置 Redis 连接。默认配置为：
- 主机：localhost
- 端口：6379
- 数据库：0

## 📊 第五步：缓存统计和监控

fn_cache 提供了强大的监控功能：

```python
from fn_cache import (
    cached, 
    get_cache_statistics, 
    start_cache_memory_monitoring
)

# 启动内存监控（每5分钟报告一次）
start_cache_memory_monitoring(interval_seconds=300)

@cached(ttl_seconds=60)
def monitored_function(x: int):
    return x * x

# 调用函数几次
for i in range(5):
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
```

## 🔧 第六步：自定义缓存键

您可以自定义缓存键的生成方式：

```python
@cached(
    ttl_seconds=300,
    key_func=lambda *args, **kwargs: f"custom_key:{args[0]}:{kwargs.get('version', 'v1')}"
)
def get_versioned_data(data_id: str, version: str = "v1"):
    print(f"获取版本化数据: {data_id} (版本: {version})")
    return f"数据_{data_id}_版本_{version}"
```

## 🎛️ 第七步：全局缓存控制

fn_cache 支持全局开关控制：

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
print(controlled_function(5))  # 执行并缓存
print(controlled_function(5))  # 命中缓存

# 禁用全局缓存
disable_global_cache()
print(f"缓存已禁用: {is_global_cache_enabled()}")

print(controlled_function(5))  # 再次执行（缓存被禁用）

# 重新启用缓存
enable_global_cache()
print(f"缓存已启用: {is_global_cache_enabled()}")
```

## 📝 完整示例

下面是一个完整的示例，展示了 fn_cache 的主要功能：

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
    print("=== fn_cache 快速上手示例 ===\n")
    
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

恭喜！您已经掌握了 fn_cache 的基本用法。接下来建议您：

1. **深入核心概念**：
   - 了解 [缓存装饰器](concepts/decorators.md) 的详细配置
   - 学习 [缓存管理器](concepts/manager.md) 的使用
   - 掌握 [存储后端](concepts/storages.md) 的配置

2. **探索进阶功能**：
   - [缓存预热](advanced/preloading.md) - 服务启动时预加载数据
   - [内存监控](advanced/memory_monitoring.md) - 监控缓存内存使用
   - [自定义存储](advanced/custom_storage.md) - 扩展存储后端

3. **查看完整示例**：
   - [基础示例](examples/basic.md) - 更多基础用法
   - [综合示例](examples/comprehensive.md) - 完整功能演示

4. **参考API文档**：
   - [装饰器API](api/decorators.md) - 完整的参数说明
   - [管理器API](api/manager.md) - 底层API使用

如果您在使用过程中遇到问题，请查看 [常见问题](faq.md) 或 [故障排除](troubleshooting.md) 指南。 