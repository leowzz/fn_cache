# 装饰器 API 参考

本文档详细介绍了 `@cached` 装饰器的完整 API。

## 📋 类定义

```python
class cached:
    """
    通用缓存装饰器类
    
    支持同步和异步函数，提供多种缓存策略和存储后端。
    """
```

## 🔧 构造函数

```python
def __init__(
    self,
    cache_type: CacheType = CacheType.TTL,
    storage_type: StorageType = StorageType.MEMORY,
    ttl_seconds: int = 60 * 10,  # 默认10分钟
    max_size: int = 1000,
    key_func: Optional[Callable] = None,
    prefix: str = DEFAULT_PREFIX,
    preload_provider: Optional[Callable[[], Iterable[tuple[tuple, dict]]]] = None,
    serializer_type: Optional[SerializerType] = None,
    serializer_kwargs: Optional[dict] = None,
    make_expire_sec_func: Optional[Callable] = None,
):
    """
    初始化缓存装饰器
    
    Args:
        cache_type: 缓存类型，TTL 或 LRU
        storage_type: 存储类型，MEMORY 或 REDIS
        ttl_seconds: TTL 缓存的过期时间（秒）
        max_size: LRU 缓存的最大容量
        key_func: 自定义缓存键生成函数
        prefix: 缓存键前缀
        preload_provider: 缓存预热数据提供者
        serializer_type: 序列化器类型
        serializer_kwargs: 序列化器参数
        make_expire_sec_func: 动态过期时间计算函数
    """
```

## 📝 参数详解

### cache_type: CacheType

缓存策略类型。

**可选值：**
- `CacheType.TTL` (默认) - 基于时间的过期策略
- `CacheType.LRU` - 最近最少使用淘汰策略

**示例：**
```python
from fn_cache import cached, CacheType

@cached(cache_type=CacheType.TTL, ttl_seconds=300)
def ttl_cached_func(x: int):
    return x * 2

@cached(cache_type=CacheType.LRU, max_size=100)
def lru_cached_func(x: int):
    return x * 2
```

### storage_type: StorageType

存储后端类型。

**可选值：**
- `StorageType.MEMORY` (默认) - 内存存储
- `StorageType.REDIS` - Redis 存储

**示例：**
```python
from fn_cache import cached, StorageType

@cached(storage_type=StorageType.MEMORY)
def memory_cached_func(x: int):
    return x * 2

@cached(storage_type=StorageType.REDIS)
def redis_cached_func(x: int):
    return x * 2
```

### ttl_seconds: int

TTL 缓存的过期时间，以秒为单位。

**默认值：** `600` (10分钟)

**示例：**
```python
@cached(ttl_seconds=60)      # 1分钟
@cached(ttl_seconds=3600)    # 1小时
@cached(ttl_seconds=86400)   # 24小时
```

### max_size: int

LRU 缓存的最大容量。

**默认值：** `1000`

**示例：**
```python
@cached(cache_type=CacheType.LRU, max_size=100)
def lru_cached_func(x: int):
    return x * 2
```

### key_func: Optional[Callable]

自定义缓存键生成函数。

**签名：** `key_func(*args, **kwargs) -> str`

**示例：**
```python
# 使用 lambda 函数
@cached(
    key_func=lambda *args, **kwargs: f"custom:{args[0]}:{kwargs.get('v', 'v1')}"
)
def custom_key_func(x: int, v: str = "v1"):
    return x * 2

# 使用普通函数
def my_key_func(*args, **kwargs):
    user_id = args[0]
    version = kwargs.get('version', 'v1')
    return f"user:{user_id}:{version}"

@cached(key_func=my_key_func)
def user_func(user_id: int, version: str = "v1"):
    return {"user_id": user_id, "version": version}
```

### prefix: str

缓存键前缀。

**默认值：** `"fn_cache:"`

**示例：**
```python
@cached(prefix="myapp:users:")
def get_user(user_id: int):
    return {"user_id": user_id}

# 生成的缓存键：myapp:users:get_user:123
```

### preload_provider: Optional[Callable]

缓存预热数据提供者函数。

**签名：** `preload_provider() -> Iterable[tuple[tuple, dict]]`

**返回值：** 返回参数元组的迭代器，每个元组包含 `(args, kwargs)`

**示例：**
```python
def user_ids_provider():
    """提供需要预加载的用户ID"""
    user_ids = [1, 2, 3, 4, 5]
    for user_id in user_ids:
        yield (user_id,), {}  # (args, kwargs)

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

### serializer_type: Optional[SerializerType]

序列化器类型。

**可选值：**
- `SerializerType.JSON` (默认) - JSON 序列化
- `SerializerType.PICKLE` - Pickle 序列化
- `SerializerType.MESSAGEPACK` - MessagePack 序列化
- `SerializerType.STRING` - 字符串序列化

**示例：**
```python
from fn_cache import cached, SerializerType

@cached(serializer_type=SerializerType.JSON)
def json_cached_func(x: int):
    return {"value": x}

@cached(serializer_type=SerializerType.PICKLE)
def pickle_cached_func(x: int):
    return ComplexObject(x)
```

### serializer_kwargs: Optional[dict]

序列化器的额外参数。

**示例：**
```python
@cached(
    serializer_type=SerializerType.JSON,
    serializer_kwargs={"ensure_ascii": False, "indent": 2}
)
def json_cached_func(x: int):
    return {"value": x, "中文": "测试"}
```

### make_expire_sec_func: Optional[Callable]

动态过期时间计算函数。

**签名：** `make_expire_sec_func(result) -> int`

**参数：**
- `result`: 函数的返回值

**返回值：** 过期时间（秒）

**示例：**
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
    is_vip = user_id % 3 == 0
    return {"user_id": user_id, "is_vip": is_vip}
```

## 🔄 调用方法

### __call__(func: Callable) -> Callable

装饰器调用方法，返回包装后的函数。

**参数：**
- `func`: 要装饰的函数

**返回值：** 装饰后的函数

**示例：**
```python
@cached(ttl_seconds=300)
def my_function(x: int):
    return x * 2

# 等价于：
def my_function(x: int):
    return x * 2
my_function = cached(ttl_seconds=300)(my_function)
```

## 🎛️ 装饰器方法

装饰后的函数具有以下额外方法：

### decorator()

直接调用装饰器，支持更多控制参数。

**签名：**
```python
async def decorator(
    self,
    func: Callable,
    *args,
    cache_read: bool = True,
    cache_write: bool = True,
    wait_for_write: bool = True,
    **kwargs,
) -> Any:
```

**参数：**
- `func`: 要执行的函数
- `*args`: 函数参数
- `cache_read`: 是否读取缓存
- `cache_write`: 是否写入缓存
- `wait_for_write`: 是否等待缓存写入完成
- `**kwargs`: 函数关键字参数

**示例：**
```python
@cached(ttl_seconds=300)
def get_data(key: str):
    return f"数据_{key}"

# 跳过缓存读取
result = await get_data.decorator(get_data, "test", cache_read=False)

# 跳过缓存写入
result = await get_data.decorator(get_data, "test", cache_write=False)
```

## 📊 缓存管理器访问

装饰后的函数可以通过 `.cache` 属性访问缓存管理器：

```python
@cached(ttl_seconds=300)
def cached_function(x: int):
    return x * 2

# 获取缓存管理器
manager = cached_function.cache

# 清除该函数的缓存
await manager.clear()

# 获取缓存统计
stats = manager.get_statistics()
```

## 🔧 缓存控制参数

在调用装饰后的函数时，可以传递以下控制参数：

### cache_read: bool

是否读取缓存。

**默认值：** `True`

**示例：**
```python
@cached(ttl_seconds=300)
def get_data(key: str):
    return f"数据_{key}"

# 正常使用缓存
result1 = get_data("test")

# 跳过缓存读取，强制执行函数
result2 = get_data("test", cache_read=False)
```

### cache_write: bool

是否写入缓存。

**默认值：** `True`

**示例：**
```python
# 跳过缓存写入，不缓存结果
result = get_data("test", cache_write=False)
```

### wait_for_write: bool

是否等待缓存写入完成（仅异步函数）。

**默认值：** `True`

**示例：**
```python
@cached(ttl_seconds=300)
async def async_get_data(key: str):
    return f"数据_{key}"

# 等待缓存写入完成
result1 = await async_get_data("test", wait_for_write=True)

# 不等待缓存写入完成
result2 = await async_get_data("test", wait_for_write=False)
```

## 📈 性能监控

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

### 启用内存监控

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

## 🎯 完整示例

```python
import asyncio
from fn_cache import cached, CacheType, StorageType, SerializerType

# 1. 基本TTL缓存
@cached(ttl_seconds=300)
def basic_ttl_cache(x: int):
    return x * 2

# 2. LRU缓存
@cached(cache_type=CacheType.LRU, max_size=100)
def lru_cache(x: int):
    return x * 2

# 3. Redis存储
@cached(
    storage_type=StorageType.REDIS,
    serializer_type=SerializerType.JSON,
    ttl_seconds=3600
)
def redis_cache(x: int):
    return {"value": x * 2}

# 4. 自定义缓存键
@cached(
    key_func=lambda *args, **kwargs: f"custom:{args[0]}:{kwargs.get('v', 'v1')}",
    ttl_seconds=300
)
def custom_key_cache(x: int, v: str = "v1"):
    return {"value": x * 2, "version": v}

# 5. 动态过期时间
def dynamic_ttl(result):
    return 3600 if result.get("is_vip") else 300

@cached(
    ttl_seconds=300,
    make_expire_sec_func=dynamic_ttl
)
def dynamic_ttl_cache(user_id: int):
    is_vip = user_id % 3 == 0
    return {"user_id": user_id, "is_vip": is_vip}

# 6. 缓存预热
def data_provider():
    for i in range(5):
        yield (i,), {}

@cached(
    ttl_seconds=3600,
    preload_provider=data_provider
)
def preload_cache(x: int):
    return f"预加载数据_{x}"

# 7. 异步函数
@cached(ttl_seconds=300)
async def async_cache(x: int):
    await asyncio.sleep(0.1)
    return x * 2

async def main():
    # 测试各种缓存
    print(basic_ttl_cache(5))
    print(lru_cache(5))
    print(redis_cache(5))
    print(custom_key_cache(5, "v2"))
    print(dynamic_ttl_cache(6))
    print(await async_cache(5))
    
    # 预加载缓存
    await preload_all_caches()

if __name__ == "__main__":
    asyncio.run(main())
```

## 🐛 错误处理

装饰器会自动处理常见的错误情况：

1. **缓存读取失败**：自动降级到执行原函数
2. **缓存写入失败**：记录错误但不影响函数执行
3. **序列化失败**：使用默认序列化器或跳过缓存
4. **Redis 连接失败**：自动降级到内存存储

## 📚 相关链接

- [缓存装饰器概念](../concepts/decorators.md) - 概念和用法说明
- [缓存管理器API](manager.md) - 底层管理器API
- [存储后端API](storages.md) - 存储后端API
- [配置API](config.md) - 配置类API 