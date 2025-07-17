# Leo Cache 示例文件

本目录包含了 Leo Cache 库的完整示例，展示了各种功能特性和使用模式。

## 示例文件说明

### 1. `comprehensive_example.py` - 完整功能演示
**功能特点：**
- 展示所有存储后端（内存、Redis）
- 展示所有序列化类型（JSON、Pickle、MessagePack）
- 完整的业务场景模拟
- 内存监控和统计功能
- 性能测试和对比

**适用场景：**
- 需要了解完整功能的开发者
- 有Redis环境的用户
- 想要进行性能测试的场景

**运行方式：**
```bash
# 确保Redis服务已启动
redis-server

# 运行示例
python examples/comprehensive_example.py
```

### 2. `simple_comprehensive_example.py` - 简化版功能演示
**功能特点：**
- 仅使用内存存储，无需外部依赖
- 展示核心功能特性
- 适合快速上手和测试
- 包含所有主要功能演示

**适用场景：**
- 初次接触Leo Cache的开发者
- 没有Redis环境的用户
- 快速功能验证和测试

**运行方式：**
```bash
# 直接运行，无需额外依赖
python examples/simple_comprehensive_example.py
```

## 功能特性展示

### 1. 多种存储后端
- **内存存储**：快速访问，适合临时数据
- **Redis存储**：分布式缓存，适合生产环境

### 2. 多种序列化类型
- **JSON序列化**：适合简单数据结构，可读性好
- **Pickle序列化**：适合复杂Python对象
- **MessagePack序列化**：高效二进制序列化，适合大数据量

### 3. 装饰器模式
```python
@cached(ttl_seconds=600, storage_type=StorageType.MEMORY)
async def get_product_info(self, product_id: str) -> Dict[str, Any]:
    # 函数逻辑
    pass
```

### 4. 自定义缓存键生成
```python
@cached(
    ttl_seconds=1800,
    key_func=lambda *args, **kwargs: f"hot_products:{datetime.now().strftime('%Y%m%d')}"
)
async def get_hot_products(self) -> List[Dict[str, Any]]:
    # 函数逻辑
    pass
```

### 5. 内存监控和统计
- 实时内存使用监控
- 缓存命中率统计
- 性能指标收集

### 6. 全局缓存开关
```python
# 禁用全局缓存
disable_global_cache()

# 启用全局缓存
enable_global_cache()

# 检查状态
is_enabled = is_global_cache_enabled()
```

### 7. 缓存预热和批量操作
- 系统启动时预加载热点数据
- 批量缓存操作
- 智能缓存策略

### 8. 缓存清除功能
- 清除特定函数的缓存：`cached_func.cache.clear()`
- 清除所有缓存：`await invalidate_all_caches()`
- 精确控制缓存生命周期

## 业务场景模拟

示例中模拟了典型的电商业务场景：

### 用户服务 (UserService)
- **用户资料管理**：使用不同序列化类型存储用户信息
- **订单管理**：处理复杂的订单数据结构
- **偏好设置**：个性化用户配置

### 商品服务 (ProductService)
- **商品信息**：基础商品数据缓存
- **分类商品**：分页查询结果缓存
- **热门商品**：动态更新的热点数据

## 性能优化策略

### 1. 序列化选择策略
- **JSON**：简单数据，需要可读性
- **Pickle**：复杂对象，Python专用
- **MessagePack**：大数据量，性能优先

### 2. 缓存策略
- **TTL策略**：基于时间的过期策略
- **LRU策略**：最近最少使用策略
- **动态TTL**：根据数据特征动态调整过期时间

### 3. 存储选择
- **内存存储**：高频访问，小数据量
- **Redis存储**：分布式环境，大数据量

## 监控和调试

### 1. 内存监控
```python
# 启动监控
start_cache_memory_monitoring(interval_seconds=5)

# 获取使用情况
memory_usage = get_cache_memory_usage()
memory_summary = get_cache_memory_summary()

# 停止监控
stop_cache_memory_monitoring()
```

### 2. 统计信息
```python
# 获取统计信息
stats = get_cache_statistics()

# 重置统计
reset_cache_statistics()
```

### 3. 缓存管理
```python
# 清除所有缓存
await invalidate_all_caches()

# 清除特定函数的缓存
cached_func.cache.clear()

# 预热缓存
await preload_all_caches()
```

## 最佳实践

### 1. 缓存键设计
- 使用有意义的键名
- 包含版本信息
- 支持参数化

### 2. 过期时间设置
- 根据数据更新频率设置
- 考虑业务重要性
- 使用动态过期时间

### 3. 错误处理
- 缓存失效时的降级策略
- 网络异常的容错处理
- 数据一致性的保证

### 4. 性能优化
- 合理选择序列化方式
- 避免缓存穿透
- 使用批量操作

## 故障排除

### 1. 常见问题
- **Redis连接失败**：检查Redis服务状态
- **序列化错误**：确认数据类型兼容性
- **内存溢出**：调整缓存大小限制

### 2. 调试技巧
- 启用详细日志
- 使用监控工具
- 分析性能指标

## 扩展开发

### 1. 自定义序列化器
```python
class CustomSerializer(Serializer):
    def serialize(self, data):
        # 自定义序列化逻辑
        pass
    
    def deserialize(self, data):
        # 自定义反序列化逻辑
        pass
```

### 2. 自定义存储后端
```python
class CustomStorage(CacheStorage):
    async def get(self, key: str):
        # 自定义获取逻辑
        pass
    
    async def set(self, key: str, value: Any, ttl_seconds: int = None):
        # 自定义设置逻辑
        pass
```

### 3. 自定义缓存策略
```python
def custom_cache_strategy(data: Any) -> int:
    # 自定义缓存策略逻辑
    return ttl_seconds
```

## 总结

这些示例文件展示了 Leo Cache 库的强大功能和灵活性。通过不同的配置组合，可以满足各种业务场景的需求。建议从简化版示例开始，逐步探索更复杂的功能特性。 