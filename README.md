# l_cache: 轻量级通用缓存库

`l_cache` 是一个专为现代 Python 应用设计的轻量级缓存库，提供统一的接口、多种缓存策略和存储后端。无论您需要简单的内存缓存还是分布式 Redis 缓存，`l_cache` 都能轻松应对。

## ✨ 核心特性

- **多种缓存策略**: 支持 TTL (Time-To-Live) 和 LRU (Least Recently Used) 缓存淘汰策略
- **灵活的存储后端**: 内置内存和 Redis 两种存储后端，可根据需求轻松切换
- **版本控制机制**: 通过全局版本号实现一键失效所有缓存，便于调试和管理
- **用户级别版本控制**: 支持按用户失效缓存，适用于多用户应用场景
- **缓存键枚举**: 支持定义结构化的缓存键模板，提高代码可维护性
- **动态过期时间**: 支持根据缓存值动态计算过期时间
- **强大的装饰器**: 提供 `u_l_cache` 和 `l_user_cache` 装饰器，支持丰富的配置，并与同步/异步函数无缝集成
- **缓存预加载**: 支持在服务启动时预先加载数据到内存缓存，提升应用初始性能
- **健壮的错误处理**: 内置 Redis 超时和连接错误处理，确保缓存问题不影响核心业务逻辑

## 🚀 快速上手

### 1. 基本用法: `u_l_cache` 装饰器

使用 `u_l_cache` 装饰器，可以轻松为函数添加缓存功能。

```python
from app.common.utils.l_cache import u_l_cache


# 使用内存TTL缓存 (默认)
@u_l_cache(ttl_seconds=60)
def get_some_data(user_id: int):
    print("正在执行复杂的数据查询...")
    return f"这是用户 {user_id} 的数据"


# 第一次调用，函数会执行
get_some_data(123)  # 输出: "正在执行复杂的数据查询..."

# 第二次调用，直接从缓存返回
get_some_data(123)  # 无输出
```

### 2. 缓存键枚举装饰器: `l_user_cache`

使用 `l_user_cache` 装饰器，可以基于预定义的缓存键模板进行缓存，支持用户级别版本控制。

```python
from app.common.utils.l_cache import l_user_cache, CacheKeyEnum, StorageType


# 定义缓存键枚举
class UserCacheKeyEnum(CacheKeyEnum):
    USER_VIP_INFO = "user:vip:info:{user_id}"
    USER_PROFILE = "user:profile:{user_id}:{tenant_id}"


# 使用缓存键枚举装饰器
@l_user_cache(
    cache_key=UserCacheKeyEnum.USER_VIP_INFO,
    key_params=["user_id"],
    make_expire_sec_func=lambda result: 3600 if result.get("is_vip") else 1800
)
async def get_user_vip_info(user_id: int):
    print(f"正在获取用户 {user_id} 的VIP信息...")
    await asyncio.sleep(0.8)

    is_vip = user_id % 3 == 0
    return {
        "user_id": user_id,
        "is_vip": is_vip,
        "vip_level": "gold" if is_vip else "none"
    }
```

### 3. 异步函数支持

```python
@u_l_cache(ttl_seconds=300)
async def fetch_user_data(user_id: int):
    print(f"正在从数据库获取用户 {user_id} 的数据...")
    await asyncio.sleep(1)  # 模拟数据库查询延迟
    return {
        "user_id": user_id,
        "name": f"User_{user_id}",
        "email": f"user{user_id}@example.com"
    }
```

### 4. 缓存预加载

对于需要快速响应的内存缓存数据，可以使用预加载功能，在服务启动时就将热点数据加载到缓存中。

```python
from app.common.utils.l_cache import u_l_cache, preload_all_caches
import asyncio


# 1. 定义一个数据提供者函数
def user_ids_provider():
    # 这些ID可以是来自配置、数据库或其他来源
    for user_id in [1, 2, 3]:
        yield (user_id,), {}  # (args, kwargs)


# 2. 在装饰器中指定 preload_provider
@u_l_cache(storage_type='memory', preload_provider=user_ids_provider)
def get_user_name(user_id: int):
    print(f"从数据库查询用户 {user_id}...")
    return f"用户_{user_id}"


# 3. 在应用启动时，调用预加载函数
async def main():
    await preload_all_caches()

    # 此时，数据已在缓存中，函数不会再次执行
    print(get_user_name(1))  # 直接输出 "用户_1"
    print(get_user_name(2))  # 直接输出 "用户_2"


if __name__ == "__main__":
    asyncio.run(main())
```

## 📚 API 参考

### `u_l_cache` 装饰器类

这是 `l_cache` 的核心装饰器。

**参数**:

- `cache_type` (`CacheType`): 缓存类型，`CacheType.TTL` (默认) 或 `CacheType.LRU`
- `storage_type` (`StorageType`): 存储类型，`StorageType.MEMORY` (默认) 或 `StorageType.REDIS`
- `ttl_seconds` (`int`): TTL 缓存的过期时间（秒），默认为 600
- `max_size` (`int`): LRU 缓存的最大容量，默认为 1000
- `key_func` (`Callable`): 自定义缓存键生成函数。接收与被装饰函数相同的参数
- `key_params` (`list[str]`): 用于自动生成缓存键的参数名列表
- `prefix` (`str`): 缓存键的前缀，默认为 `"cache:"`
- `preload_provider` (`Callable`): 一个函数，返回一个可迭代对象，用于缓存预加载。迭代的每个元素都是一个 `(args, kwargs)` 元组

### `l_user_cache` 装饰器类

基于缓存键枚举的装饰器，支持用户级别版本控制。

**参数**:

- `cache_key` (`CacheKeyEnum`): 缓存键枚举实例
- `storage_type` (`StorageType`): 存储类型，默认为 `StorageType.REDIS`
- `make_expire_sec_func` (`Callable`): 动态生成过期时间的函数，接收缓存值作为参数
- `key_params` (`list[str]`): 需要从函数参数中获取的key参数名列表
- `prefix` (`str`): 缓存key前缀，默认为 `"l_cache:"`
- `user_id_param` (`str`): 用户ID参数名，用于从函数参数中提取用户ID，默认为 `"user_id"`

### `CacheKeyEnum` 基类

缓存键枚举基类，用于定义结构化的缓存键模板。

```python
class CacheKeyEnum(str, Enum):
    """缓存键枚举基类"""
    
    def format(self, **kwargs) -> str:
        """格式化缓存键，替换模板中的参数"""
        return self.value.format(**kwargs)
```

### `UniversalCacheManager` 类

提供了所有底层缓存操作的接口。

**核心方法**:

- `get(key, user_id=None)`: (异步) 获取缓存
- `set(key, value, ttl_seconds=None, user_id=None)`: (异步) 设置缓存
- `delete(key)`: (异步) 删除缓存
- `get_sync(key, user_id=None)` / `set_sync(...)` / `delete_sync(key)`: 内存缓存的同步版本
- `increment_global_version()`: (异步) 递增全局版本号，使所有缓存失效
- `increment_user_version(user_id)`: (异步) 递增用户版本号，使该用户的所有缓存失效
- `invalidate_all()`: (异步) 使所有缓存失效
- `invalidate_user_cache(user_id)`: (异步) 使用户的所有缓存失效

**核心属性**:

- `is_global_cache_enabled_sync` (`bool`): (同步) 检查内存缓存是否已启用

### 全局控制函数

- `preload_all_caches()`: (异步) 执行所有已注册的缓存预加载任务
- `invalidate_all_caches()`: (异步) 失效所有使用默认管理器的缓存
- `invalidate_user_cache(user_id)`: (异步) 使用户的所有缓存失效

## ⚙️ 高级用法

### 切换到 Redis 存储

只需更改 `storage_type` 参数即可。

```python
@u_l_cache(storage_type=StorageType.REDIS, ttl_seconds=3600)
async def get_shared_data():
    # ... 从数据库或RPC获取数据 ...
    return {"data": "some shared data"}
```

### 使用 LRU 缓存策略

```python
@u_l_cache(
    cache_type=CacheType.LRU,
    max_size=100,
    storage_type=StorageType.MEMORY
)
def calculate_fibonacci(n: int) -> int:
    """计算斐波那契数列（同步函数示例）"""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
```

### 自定义缓存键

对于复杂的参数，可以提供自定义的 `key_func`。

```python
def make_user_key(user: User):
    return f"user_cache:{user.org_id}:{user.id}"

@u_l_cache(key_func=make_user_key)
def get_user_permissions(user: User):
    # ...
    return ["perm1", "perm2"]
```

或者，使用 `key_params` 自动生成。

```python
@u_l_cache(key_params=['user_id', 'tenant_id'])
def get_document(doc_id: int, user_id: int, tenant_id: str):
    # 自动生成的key类似于: "app.module.get_document:user_id=123:tenant_id=abc"
    pass
```

### 用户级别缓存管理

```python
from app.common.utils.l_cache import UniversalCacheManager, CacheConfig, StorageType

class UserCacheService:
    def __init__(self):
        config = CacheConfig(
            storage_type=StorageType.REDIS,
            prefix="user_cache:"
        )
        self.cache = UniversalCacheManager(config)
    
    async def get_user_data(self, user_id: int):
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
```

### 动态过期时间

```python
@l_user_cache(
    cache_key=UserCacheKeyEnum.USER_VIP_INFO,
    key_params=["user_id"],
    make_expire_sec_func=lambda result: 3600 if result.get("is_vip") else 1800
)
async def get_user_vip_info(user_id: int):
    # VIP用户缓存1小时，普通用户缓存30分钟
    pass
```

### 多参数缓存键

```python
@l_user_cache(
    cache_key=UserCacheKeyEnum.USER_PROFILE,
    key_params=["user_id", "tenant_id"],
    storage_type=StorageType.REDIS
)
async def get_user_profile(user_id: int, tenant_id: str):
    # 支持多租户的用户资料缓存
    pass
```

## 🔧 配置选项

### CacheConfig 配置类

```python
from app.common.utils.l_cache import CacheConfig, CacheType, StorageType

config = CacheConfig(
    cache_type=CacheType.TTL,      # 缓存策略: TTL 或 LRU
    storage_type=StorageType.MEMORY,  # 存储后端: MEMORY 或 REDIS
    ttl_seconds=600,               # TTL 过期时间（秒）
    max_size=1000,                 # LRU 最大容量
    prefix="cache:",               # 缓存键前缀
    global_version_key="l_cache:global:version",  # 全局版本号键
    user_version_key="l_cache:user:version:{user_id}",  # 用户版本号键
    make_expire_sec_func=None      # 动态过期时间函数
)
```

## 💡 设计理念

- **统一接口**: `UniversalCacheManager` 提供了统一的接口，屏蔽了不同存储后端的实现细节
- **版本控制**: 通过全局版本号机制实现一键失效所有缓存，便于调试和管理
- **用户级别控制**: 支持按用户失效缓存，适用于多用户应用场景
- **结构化缓存键**: 通过枚举定义缓存键模板，提高代码可维护性和一致性
- **装饰器模式**: `u_l_cache` 和 `l_user_cache` 使用装饰器模式，以非侵入的方式为函数添加缓存逻辑
- **错误隔离**: 内置 Redis 超时和连接错误处理，确保缓存问题不影响核心业务逻辑
- **性能优化**: 支持缓存预加载和动态过期时间，提升应用性能

## 📝 使用示例

更多详细的使用示例，请参考 `examples.py` 文件，其中包含了：

- 基本的装饰器使用
- 缓存键枚举和用户级别版本控制
- 直接使用缓存管理器
- 不同的存储后端配置
- 自定义key生成策略
- 缓存预加载功能
- 全局缓存控制
- 动态过期时间配置

## 🔍 版本信息

- **版本**: 1.0.0
- **作者**: WangZhanze <wangzhanze@huoban.ai>
- **描述**: 轻量级通用缓存库
