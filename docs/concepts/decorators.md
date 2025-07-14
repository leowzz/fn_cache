# 缓存装饰器

`@cached` 装饰器是 fn_cache 的核心功能，它允许您轻松地为任何函数添加缓存能力。

## 🎯 基本概念

缓存装饰器的工作原理：

1. **函数调用拦截**：装饰器拦截对被装饰函数的调用
2. **缓存键生成**：根据函数参数生成唯一的缓存键
3. **缓存查找**：检查缓存中是否存在对应的值
4. **缓存命中**：如果存在且未过期，直接返回缓存值
5. **缓存未命中**：如果不存在或已过期，执行原函数并缓存结果

## 📝 基本用法

### 最简单的用法

```python
from fn_cache import cached

@cached(ttl_seconds=300)  # 缓存5分钟
def get_user_data(user_id: int):
    # 模拟数据库查询
    return {"user_id": user_id, "name": f"用户_{user_id}"}
```

### 异步函数支持

```python
@cached(ttl_seconds=300)
async def fetch_user_data(user_id: int):
    # 模拟异步数据库查询
    await asyncio.sleep(1)
    return {"user_id": user_id, "name": f"用户_{user_id}"}
```

## ⚙️ 配置参数

### 缓存策略配置

#### TTL 缓存（默认）

```python
from fn_cache import cached, CacheType

@cached(
    cache_type=CacheType.TTL,
    ttl_seconds=600  # 10分钟后过期
)
def get_temporary_data(key: str):
    return f"临时数据_{key}"
```

#### LRU 缓存

```python
@cached(
    cache_type=CacheType.LRU,
    max_size=1000  # 最多缓存1000个条目
)
def get_cached_data(key: str):
    return f"数据_{key}"
```

### 存储后端配置

#### 内存存储（默认）

```python
from fn_cache import cached, StorageType

@cached(
    storage_type=StorageType.MEMORY,
    ttl_seconds=300
)
def get_memory_cached_data(key: str):
    return f"内存缓存数据_{key}"
```

#### Redis 存储

```python
@cached(
    storage_type=StorageType.REDIS,
    ttl_seconds=3600,  # 1小时
    prefix="myapp:"  # 自定义前缀
)
def get_redis_cached_data(key: str):
    return f"Redis缓存数据_{key}"
```

### 序列化配置

```python
from fn_cache import cached, SerializerType

# JSON 序列化（默认）
@cached(
    serializer_type=SerializerType.JSON,
    ttl_seconds=300
)
def get_json_data(key: str):
    return {"key": key, "value": f"值_{key}"}

# Pickle 序列化（支持复杂对象）
@cached(
    serializer_type=SerializerType.PICKLE,
    ttl_seconds=300
)
def get_complex_data(key: str):
    return ComplexObject(key)

# MessagePack 序列化（高效）
@cached(
    serializer_type=SerializerType.MESSAGEPACK,
    ttl_seconds=300
)
def get_efficient_data(key: str):
    return {"key": key, "data": [1, 2, 3, 4, 5]}
```

## 🔑 缓存键配置

### 默认缓存键生成

默认情况下，fn_cache 会根据函数名和所有参数生成缓存键：

```python
@cached(ttl_seconds=300)
def get_user_info(user_id: int, include_profile: bool = True):
    return {"user_id": user_id, "profile": include_profile}

# 缓存键格式：fn_cache:get_user_info:123:True
```

### 自定义缓存键函数

```python
@cached(
    ttl_seconds=300,
    key_func=lambda *args, **kwargs: f"user:{args[0]}:{kwargs.get('version', 'v1')}"
)
def get_user_data(user_id: int, version: str = "v1"):
    return {"user_id": user_id, "version": version}

# 缓存键格式：user:123:v1
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
    return {"user_id": user_id, "profile": "用户资料"}
```

## 🎛️ 高级配置

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
    return f"用户_{user_id}"

# 在应用启动时预加载
async def startup():
    from fn_cache import preload_all_caches
    await preload_all_caches()
```

### 自定义前缀

```python
@cached(
    ttl_seconds=300,
    prefix="myapp:users:"
)
def get_user_data(user_id: int):
    return {"user_id": user_id, "name": f"用户_{user_id}"}

# 缓存键格式：myapp:users:get_user_data:123
```

## 🔧 装饰器方法

装饰后的函数具有一些额外的方法：

```python
@cached(ttl_seconds=300)
def cached_function(x: int):
    return x * 2

# 获取缓存管理器
manager = cached_function.cache

# 清除该函数的缓存
cached_function.cache.clear()

# 获取缓存统计
stats = cached_function.cache.get_statistics()
```

## 🚫 缓存控制

### 跳过缓存读取

```python
@cached(ttl_seconds=300)
def get_data(key: str):
    return f"数据_{key}"

# 正常使用缓存
result1 = get_data("test")

# 跳过缓存读取，强制执行函数
result2 = get_data("test", cache_read=False)
```

### 跳过缓存写入

```python
# 跳过缓存写入，不缓存结果
result = get_data("test", cache_write=False)
```

### 等待缓存写入

```python
# 异步函数中等待缓存写入完成
result = await get_data("test", wait_for_write=True)
```

## 📊 性能监控

### 启用统计

```python
@cached(
    ttl_seconds=300,
    enable_statistics=True  # 默认启用
)
def monitored_function(x: int):
    return x * x

# 获取统计信息
from fn_cache import get_cache_statistics
stats = get_cache_statistics()
```

### 内存监控

```python
@cached(
    ttl_seconds=300,
    enable_memory_monitoring=True  # 默认启用
)
def memory_monitored_function(x: int):
    return x * x

# 启动内存监控
from fn_cache import start_cache_memory_monitoring
start_cache_memory_monitoring(interval_seconds=300)
```

## 🔄 版本控制

### 全局版本控制

```python
from fn_cache import invalidate_all_caches

@cached(ttl_seconds=3600)
def get_config_data():
    return {"version": "1.0", "settings": {...}}

# 使所有缓存失效
await invalidate_all_caches()
```

### 用户级版本控制

```python
from fn_cache import UniversalCacheManager

manager = UniversalCacheManager()

# 递增用户版本号
await manager.increment_user_version("user123")

# 使用户的所有缓存失效
await manager.invalidate_user_cache("user123")
```

## 🎯 最佳实践

### 1. 选择合适的缓存策略

- **TTL 缓存**：适用于数据有明确过期时间的场景
- **LRU 缓存**：适用于内存有限，需要自动淘汰的场景

### 2. 合理设置缓存时间

```python
# 静态数据 - 长时间缓存
@cached(ttl_seconds=86400)  # 24小时
def get_static_config():
    return {"app_name": "MyApp", "version": "1.0"}

# 动态数据 - 短时间缓存
@cached(ttl_seconds=60)  # 1分钟
def get_user_status(user_id: int):
    return {"user_id": user_id, "online": True}
```

### 3. 使用有意义的缓存键

```python
# 好的做法
@cached(
    key_func=lambda *args, **kwargs: f"user:{args[0]}:profile"
)
def get_user_profile(user_id: int):
    return {"user_id": user_id, "profile": "..."}

# 避免的做法
@cached()  # 使用默认键，可能不够清晰
def get_user_profile(user_id: int):
    return {"user_id": user_id, "profile": "..."}
```

### 4. 处理缓存异常

```python
@cached(ttl_seconds=300)
def get_data_with_fallback(key: str):
    try:
        # 尝试从缓存获取
        return get_data_from_cache(key)
    except Exception:
        # 缓存失败时的降级处理
        return get_data_from_source(key)
```

### 5. 监控缓存性能

```python
# 定期检查缓存命中率
import asyncio
from fn_cache import get_cache_statistics

async def monitor_cache():
    while True:
        stats = get_cache_statistics()
        for cache_id, cache_stats in stats.items():
            hit_rate = cache_stats['hit_rate']
            if hit_rate < 0.5:  # 命中率低于50%
                print(f"警告: {cache_id} 缓存命中率过低: {hit_rate:.2%}")
        await asyncio.sleep(300)  # 每5分钟检查一次
```

## 🐛 常见问题

### 1. 缓存键冲突

**问题**：不同函数使用相同的缓存键
**解决**：使用自定义前缀或缓存键函数

```python
@cached(prefix="function1:")
def function1(x: int):
    return x * 2

@cached(prefix="function2:")
def function2(x: int):
    return x * 3
```

### 2. 缓存穿透

**问题**：大量请求查询不存在的数据
**解决**：使用空值缓存

```python
@cached(ttl_seconds=60)
def get_user_data(user_id: int):
    data = query_database(user_id)
    if data is None:
        # 缓存空值，避免缓存穿透
        return {"user_id": user_id, "exists": False}
    return data
```

### 3. 缓存雪崩

**问题**：大量缓存同时过期
**解决**：使用随机过期时间

```python
import random

@cached(
    ttl_seconds=lambda: 300 + random.randint(0, 60)  # 300-360秒随机过期
)
def get_data(key: str):
    return f"数据_{key}"
```

## 📚 相关链接

- [缓存管理器](manager.md) - 了解底层缓存管理
- [存储后端](storages.md) - 配置不同的存储后端
- [配置系统](config.md) - 详细的配置选项
- [API参考](../api/decorators.md) - 完整的API文档 