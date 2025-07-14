# 常见问题 (FAQ)

本文档回答了 fn_cache 使用过程中的常见问题。

## 🔧 安装和配置

### Q: 如何安装 fn_cache？

**A:** 使用 pip 安装：

```bash
pip install fn-cache
```

如果需要开发依赖：

```bash
pip install fn-cache[dev]
```

### Q: 支持哪些 Python 版本？

**A:** fn_cache 支持 Python 3.8 及以上版本。

### Q: 如何配置 Redis 连接？

**A:** 在装饰器中指定 Redis 配置：

```python
@cached(
    storage_type=StorageType.REDIS,
    redis_config={
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "password": "your_password",  # 可选
        "decode_responses": True
    }
)
def my_function():
    return "data"
```

### Q: 如何设置环境变量配置？

**A:** 可以通过环境变量设置默认配置：

```bash
export FN_CACHE_REDIS_HOST=localhost
export FN_CACHE_REDIS_PORT=6379
export FN_CACHE_DEFAULT_TTL=600
```

## 🎛️ 基本使用

### Q: 如何为函数添加缓存？

**A:** 使用 `@cached` 装饰器：

```python
from fn_cache import cached

@cached(ttl_seconds=300)  # 缓存5分钟
def get_user_data(user_id: int):
    return {"user_id": user_id, "name": f"用户_{user_id}"}
```

### Q: 如何缓存异步函数？

**A:** 直接使用相同的装饰器：

```python
@cached(ttl_seconds=300)
async def fetch_user_data(user_id: int):
    await asyncio.sleep(1)
    return {"user_id": user_id, "name": f"用户_{user_id}"}
```

### Q: 如何选择缓存策略？

**A:** 
- **TTL 缓存**：适用于数据有明确过期时间的场景
- **LRU 缓存**：适用于内存有限，需要自动淘汰的场景

```python
# TTL 缓存
@cached(cache_type=CacheType.TTL, ttl_seconds=300)

# LRU 缓存
@cached(cache_type=CacheType.LRU, max_size=1000)
```

### Q: 如何自定义缓存键？

**A:** 使用 `key_func` 参数：

```python
@cached(
    key_func=lambda *args, **kwargs: f"user:{args[0]}:{kwargs.get('v', 'v1')}"
)
def get_user_data(user_id: int, v: str = "v1"):
    return {"user_id": user_id, "version": v}
```

## 💾 存储后端

### Q: 内存存储和 Redis 存储有什么区别？

**A:**
- **内存存储**：速度快，但数据不持久，进程重启后丢失
- **Redis 存储**：数据持久，支持分布式，但需要额外的 Redis 服务

### Q: 如何切换存储后端？

**A:** 修改 `storage_type` 参数：

```python
# 内存存储（默认）
@cached(storage_type=StorageType.MEMORY)

# Redis 存储
@cached(storage_type=StorageType.REDIS)
```

### Q: Redis 连接失败怎么办？

**A:** fn_cache 会自动处理 Redis 连接失败：
1. 记录错误日志
2. 自动降级到内存存储
3. 不影响函数正常执行

### Q: 如何配置 Redis 集群？

**A:** 在 `redis_config` 中指定集群配置：

```python
@cached(
    storage_type=StorageType.REDIS,
    redis_config={
        "startup_nodes": [
            {"host": "redis1", "port": 6379},
            {"host": "redis2", "port": 6379},
        ],
        "decode_responses": True
    }
)
```

## 📊 序列化

### Q: 如何选择序列化器？

**A:**
- **JSON**：适合简单数据结构，可读性好
- **Pickle**：支持复杂对象，但安全性较低
- **MessagePack**：高效，适合大数据量
- **String**：适合简单字符串

```python
@cached(serializer_type=SerializerType.JSON)      # JSON
@cached(serializer_type=SerializerType.PICKLE)    # Pickle
@cached(serializer_type=SerializerType.MESSAGEPACK) # MessagePack
```

### Q: 序列化失败怎么办？

**A:** fn_cache 会自动处理序列化失败：
1. 尝试使用默认序列化器
2. 如果仍然失败，跳过缓存
3. 记录错误日志

### Q: 如何序列化自定义对象？

**A:** 使用 Pickle 序列化器：

```python
from dataclasses import dataclass
from fn_cache import cached, SerializerType

@dataclass
class UserProfile:
    user_id: int
    name: str

@cached(serializer_type=SerializerType.PICKLE)
def get_user_profile(user_id: int):
    return UserProfile(user_id=user_id, name=f"用户_{user_id}")
```

## 🔄 缓存控制

### Q: 如何禁用全局缓存？

**A:** 使用全局开关：

```python
from fn_cache import disable_global_cache, enable_global_cache

# 禁用所有缓存
disable_global_cache()

# 重新启用
enable_global_cache()
```

### Q: 如何清除特定函数的缓存？

**A:** 通过缓存管理器：

```python
@cached(ttl_seconds=300)
def my_function(x: int):
    return x * 2

# 清除该函数的缓存
my_function.cache.clear()
```

### Q: 如何使所有缓存失效？

**A:** 使用版本控制：

```python
from fn_cache import invalidate_all_caches

# 使所有缓存失效
await invalidate_all_caches()
```

### Q: 如何跳过缓存读取？

**A:** 在函数调用时传递参数：

```python
@cached(ttl_seconds=300)
def get_data(key: str):
    return f"数据_{key}"

# 跳过缓存读取，强制执行函数
result = get_data("test", cache_read=False)
```

## 📈 监控和统计

### Q: 如何查看缓存命中率？

**A:** 使用统计功能：

```python
from fn_cache import get_cache_statistics

stats = get_cache_statistics()
for cache_id, cache_stats in stats.items():
    print(f"{cache_id}: 命中率 {cache_stats['hit_rate']:.2%}")
```

### Q: 如何监控内存使用？

**A:** 启动内存监控：

```python
from fn_cache import start_cache_memory_monitoring, get_cache_memory_usage

# 启动监控（每5分钟报告）
start_cache_memory_monitoring(interval_seconds=300)

# 获取内存使用情况
memory_usage = get_cache_memory_usage()
for info in memory_usage:
    print(f"内存占用: {info.memory_mb:.2f} MB")
```

### Q: 如何重置统计信息？

**A:** 使用重置函数：

```python
from fn_cache import reset_cache_statistics

# 重置所有统计
reset_cache_statistics()

# 重置特定缓存统计
reset_cache_statistics("cache_id")
```

## 🔧 高级功能

### Q: 如何实现动态过期时间？

**A:** 使用 `make_expire_sec_func` 参数：

```python
def dynamic_ttl(result):
    return 3600 if result.get("is_vip") else 300

@cached(
    ttl_seconds=300,
    make_expire_sec_func=dynamic_ttl
)
def get_user_info(user_id: int):
    is_vip = user_id % 3 == 0
    return {"user_id": user_id, "is_vip": is_vip}
```

### Q: 如何实现缓存预热？

**A:** 使用 `preload_provider` 参数：

```python
def data_provider():
    for i in range(5):
        yield (i,), {}

@cached(
    ttl_seconds=3600,
    preload_provider=data_provider
)
def get_data(x: int):
    return f"数据_{x}"

# 在应用启动时预加载
async def startup():
    from fn_cache import preload_all_caches
    await preload_all_caches()
```

### Q: 如何实现用户级缓存失效？

**A:** 使用用户版本控制：

```python
from fn_cache import UniversalCacheManager

manager = UniversalCacheManager()

# 递增用户版本号
await manager.increment_user_version("user123")

# 使用户的所有缓存失效
await manager.invalidate_user_cache("user123")
```

## 🐛 故障排除

### Q: 缓存不生效怎么办？

**A:** 检查以下几点：
1. 确认全局缓存已启用
2. 检查缓存键是否正确
3. 确认 TTL 时间是否合理
4. 查看日志中的错误信息

### Q: 内存占用过高怎么办？

**A:** 可以采取以下措施：
1. 使用 LRU 缓存策略
2. 减少 `max_size` 参数
3. 缩短 TTL 时间
4. 使用 Redis 存储

### Q: Redis 连接超时怎么办？

**A:** 调整 Redis 配置：

```python
@cached(
    storage_type=StorageType.REDIS,
    redis_config={
        "socket_timeout": 5.0,
        "socket_connect_timeout": 5.0,
        "retry_on_timeout": True
    }
)
```

### Q: 序列化错误怎么办？

**A:** 检查数据类型是否支持：
1. JSON 只支持基本数据类型
2. Pickle 支持大多数 Python 对象
3. MessagePack 支持基本数据类型和列表/字典

### Q: 异步函数缓存不工作？

**A:** 确保正确使用 `await`：

```python
@cached(ttl_seconds=300)
async def async_function():
    return "data"

# 正确调用
result = await async_function()

# 错误调用
result = async_function()  # 返回协程对象
```

## 🔧 性能优化

### Q: 如何提高缓存命中率？

**A:** 
1. 合理设置 TTL 时间
2. 使用有意义的缓存键
3. 避免缓存过于频繁变化的数据
4. 使用缓存预热功能

### Q: 如何减少内存占用？

**A:**
1. 使用 LRU 缓存策略
2. 设置合理的 `max_size`
3. 使用 MessagePack 序列化
4. 定期清理过期缓存

### Q: 如何提高 Redis 性能？

**A:**
1. 使用连接池
2. 启用 Redis 持久化
3. 使用 Redis 集群
4. 优化网络配置

## 📚 更多帮助

### Q: 在哪里可以找到更多示例？

**A:** 查看项目中的示例文件：
- [基础示例](examples/basic.md)
- [进阶示例](examples/advanced.md)
- [综合示例](examples/comprehensive.md)

### Q: 如何报告 Bug？

**A:** 在 [GitHub Issues](https://github.com/leowzz/fn_cache/issues) 中提交问题，请包含：
1. 详细的错误信息
2. 复现步骤
3. 环境信息（Python 版本、操作系统等）

### Q: 如何贡献代码？

**A:** 欢迎提交 Pull Request！请：
1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 创建 Pull Request

### Q: 如何获取最新版本？

**A:** 使用 pip 更新：

```bash
pip install --upgrade fn-cache
```

或者从源码安装最新版本：

```bash
pip install git+https://github.com/leowzz/fn_cache.git
```

## 📞 联系支持

如果您的问题没有在这里得到解答，可以：

1. 查看 [故障排除](troubleshooting.md) 指南
2. 在 [GitHub Issues](https://github.com/leowzz/fn_cache/issues) 中搜索
3. 提交新的 Issue
4. 查看 [API 文档](../api/decorators.md) 获取详细信息 