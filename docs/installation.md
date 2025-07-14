# 安装指南

本文档将指导您如何安装和配置 fn_cache 缓存库。

## 📦 系统要求

- Python 3.8 或更高版本
- 可选：Redis 服务器（如果使用 Redis 存储后端）

## 🔧 安装方式

### 使用 pip 安装（推荐）

```bash
pip install fn-cache
```

### 从源码安装

```bash
git clone https://github.com/leowzz/fn_cache.git
cd fn_cache
pip install -e .
```

### 安装开发依赖

如果您需要运行测试或贡献代码：

```bash
pip install fn-cache[dev]
```

### 安装文档依赖

如果您需要构建文档：

```bash
pip install fn-cache[docs]
```

## 🚀 快速验证安装

安装完成后，您可以通过以下方式验证安装是否成功：

```python
# 测试基本导入
from fn_cache import cached, UniversalCacheManager
print("fn_cache 安装成功！")

# 测试基本功能
@cached(ttl_seconds=60)
def test_function(x):
    return x * 2

result = test_function(5)
print(f"测试结果: {result}")
```

## 🔌 Redis 配置（可选）

如果您计划使用 Redis 存储后端，需要安装 Redis 服务器：

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### macOS

```bash
brew install redis
brew services start redis
```

### Windows

从 [Redis 官网](https://redis.io/download) 下载 Windows 版本，或使用 WSL。

### 验证 Redis 连接

```python
from fn_cache import UniversalCacheManager, CacheConfig, StorageType

# 测试 Redis 连接
config = CacheConfig(
    storage_type=StorageType.REDIS,
    redis_config={
        "host": "localhost",
        "port": 6379,
        "db": 0
    }
)

try:
    manager = UniversalCacheManager(config)
    # 测试连接
    await manager.set("test", "value", ttl_seconds=60)
    print("Redis 连接成功！")
except Exception as e:
    print(f"Redis 连接失败: {e}")
```

## ⚙️ 环境变量配置

您可以通过环境变量配置一些默认设置：

```bash
# Redis 连接配置
export FN_CACHE_REDIS_HOST=localhost
export FN_CACHE_REDIS_PORT=6379
export FN_CACHE_REDIS_DB=0

# 默认缓存配置
export FN_CACHE_DEFAULT_TTL=600
export FN_CACHE_DEFAULT_MAX_SIZE=1000
```

## 🔧 开发环境设置

如果您想参与项目开发：

```bash
# 克隆仓库
git clone https://github.com/leowzz/fn_cache.git
cd fn_cache

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -e .[dev]

# 运行测试
pytest

# 运行代码格式化
black fn_cache/
isort fn_cache/

# 运行类型检查
mypy fn_cache/
```

## 📋 依赖项说明

### 核心依赖

- `typing-extensions>=4.0.0` - 类型提示扩展（Python < 3.9）
- `pydantic~=2.10.6` - 数据验证和配置管理
- `fastapi>0.100.0,<0.116.0` - Web 框架支持
- `loguru~=0.7.3` - 日志记录

### 可选依赖

- `redis` - Redis 客户端（使用 Redis 存储时）
- `msgpack` - MessagePack 序列化支持

### 开发依赖

- `pytest>=7.0.0` - 测试框架
- `pytest-asyncio>=0.21.0` - 异步测试支持
- `pytest-cov>=4.0.0` - 测试覆盖率
- `black>=23.0.0` - 代码格式化
- `isort>=5.12.0` - 导入排序
- `flake8>=6.0.0` - 代码检查
- `mypy>=1.0.0` - 类型检查

## 🐛 常见安装问题

### 1. 权限问题

如果遇到权限错误，可以尝试：

```bash
pip install --user fn-cache
```

### 2. Python 版本问题

确保使用 Python 3.8 或更高版本：

```bash
python --version
```

### 3. Redis 连接问题

如果 Redis 连接失败，检查：

- Redis 服务是否正在运行
- 端口是否正确（默认 6379）
- 防火墙设置
- Redis 配置中的 bind 设置

### 4. 依赖冲突

如果遇到依赖冲突，可以尝试：

```bash
pip install --upgrade pip
pip install fn-cache --force-reinstall
```

## 📞 获取帮助

如果在安装过程中遇到问题，可以：

1. 查看 [常见问题](faq.md) 页面
2. 在 [GitHub Issues](https://github.com/leowzz/fn_cache/issues) 中搜索或提交问题
3. 查看 [故障排除](troubleshooting.md) 指南

## 🎯 下一步

安装完成后，建议您：

1. 阅读 [快速上手](quickstart.md) 教程
2. 查看 [基础示例](examples/basic.md)
3. 了解 [核心概念](concepts/decorators.md) 