# fn_cache 文档

欢迎使用 fn_cache - 轻量级通用缓存库！

## 📖 文档导航

### 🚀 快速开始
- [安装指南](installation.md) - 如何安装和配置 fn_cache
- [快速上手](quickstart.md) - 5分钟快速入门教程
- [基础示例](examples/basic.md) - 基础用法示例

### 📚 核心概念
- [缓存装饰器](concepts/decorators.md) - 理解 @cached 装饰器
- [缓存管理器](concepts/manager.md) - UniversalCacheManager 详解
- [存储后端](concepts/storages.md) - 内存和Redis存储
- [配置系统](concepts/config.md) - 缓存配置详解
- [版本控制](concepts/versioning.md) - 全局和用户级版本控制

### 🔧 进阶用法
- [缓存键与序列化](advanced/keys_serialization.md) - 自定义缓存键和序列化
- [内存监控](advanced/memory_monitoring.md) - 内存占用监控
- [异步支持](advanced/async_support.md) - 异步函数缓存
- [自定义存储](advanced/custom_storage.md) - 扩展存储后端
- [缓存预热](advanced/preloading.md) - 缓存预加载功能

### 🛠️ 工具与CLI
- [CLI工具](tools/cli.md) - 命令行工具使用
- [监控工具](tools/monitoring.md) - 缓存监控和统计

### 📖 API参考
- [装饰器API](api/decorators.md) - @cached 装饰器完整API
- [管理器API](api/manager.md) - UniversalCacheManager API
- [存储API](api/storages.md) - 存储后端API
- [配置API](api/config.md) - 配置类API
- [枚举类型](api/enums.md) - 枚举类型定义
- [工具函数](api/utils.md) - 工具函数API

### 📝 示例教程
- [基础示例](examples/basic.md) - 简单缓存示例
- [进阶示例](examples/advanced.md) - 复杂场景示例
- [全局开关示例](examples/global_switch.md) - 全局缓存控制
- [内存监控示例](examples/memory_monitoring.md) - 内存监控使用
- [综合示例](examples/comprehensive.md) - 完整功能演示

### ❓ 常见问题
- [FAQ](faq.md) - 常见问题解答
- [故障排除](troubleshooting.md) - 问题诊断和解决

### 🤝 贡献指南
- [贡献指南](contributing.md) - 如何参与项目开发
- [开发环境](development.md) - 开发环境搭建
- [测试指南](testing.md) - 测试规范

## 🎯 项目特性

fn_cache 是一个专为现代 Python 应用设计的轻量级缓存库，具有以下核心特性：

- **多种缓存策略**: TTL 和 LRU 缓存淘汰策略
- **灵活的存储后端**: 内存和 Redis 存储支持
- **多种序列化格式**: JSON、Pickle、MessagePack、字符串
- **版本控制机制**: 全局和用户级缓存失效
- **强大的装饰器**: 支持同步/异步函数
- **缓存预热**: 服务启动时预加载数据
- **内存监控**: 实时内存占用监控
- **缓存统计**: 详细的性能指标

## 📦 快速安装

```bash
pip install fn-cache
```

## 🚀 快速示例

```python
from fn_cache import cached

@cached(ttl_seconds=300)
def get_user_data(user_id: int):
    # 模拟数据库查询
    return {"user_id": user_id, "name": f"User_{user_id}"}

# 第一次调用会执行函数
result1 = get_user_data(123)

# 第二次调用直接从缓存返回
result2 = get_user_data(123)  # 命中缓存
```

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](../LICENSE) 文件。

## 🔗 相关链接

- [GitHub 仓库](https://github.com/leowzz/fn_cache)
- [PyPI 包](https://pypi.org/project/fn-cache/)
- [问题反馈](https://github.com/leowzz/fn_cache/issues)
- [更新日志](https://github.com/leowzz/fn_cache/releases) 