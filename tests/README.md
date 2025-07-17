# L-Cache 测试套件

本目录包含 L-Cache 项目的完整测试套件，涵盖了所有核心功能的单元测试和集成测试。

## 测试结构

```
tests/
├── README.md                 # 测试说明文档
├── test_basic.py            # 基础功能测试
├── test_manager.py          # 缓存管理器测试
├── test_storages.py         # 存储层测试
├── test_decorators.py       # 装饰器测试
├── test_utils.py            # 工具函数测试
└── test_integration.py      # 集成测试
```

## 测试分类

### 单元测试
- **test_manager.py**: 测试 `UniversalCacheManager` 的所有功能
  - 初始化配置
  - 缓存操作（get/set/delete）
  - 版本控制
  - 用户级别缓存
  - 错误处理

- **test_storages.py**: 测试存储层实现
  - 内存存储（TTL/LRU）
  - Redis存储
  - 错误处理
  - 性能测试

- **test_decorators.py**: 测试装饰器功能
  - `cached` 装饰器
  - 缓存注册表
  - 预加载功能

- **test_utils.py**: 测试工具函数
  - 字符串化工具
  - 安全Redis操作
  - 缓存键构建
  - 序列化工具

### 集成测试
- **test_integration.py**: 端到端测试
  - 完整工作流程
  - 并发操作
  - 性能测试
  - 真实场景模拟

## 运行测试

### 安装依赖
```bash
pip install -r requirements-dev.txt
```

### 运行所有测试
```bash
# 使用pytest
pytest

# 使用测试脚本
python run_tests.py

# 详细输出
pytest -v
```

### 运行特定测试
```bash
# 只运行单元测试
python run_tests.py --unit

# 只运行集成测试
python run_tests.py --integration

# 运行特定测试文件
pytest tests/test_manager.py

# 运行特定测试类
pytest tests/test_manager.py::TestUniversalCacheManager

# 运行特定测试方法
pytest tests/test_manager.py::TestUniversalCacheManager::test_init_with_default_config
```

### 并行运行测试
```bash
# 使用4个进程并行运行
pytest -n 4

# 使用测试脚本
python run_tests.py --parallel 4
```

### 跳过慢速测试
```bash
# 跳过标记为slow的测试
pytest -m "not slow"

# 使用测试脚本
python run_tests.py --fast
```

### 生成覆盖率报告
```bash
# 生成覆盖率报告
pytest --cov=fn_cache --cov-report=html

# 使用测试脚本
python run_tests.py --coverage
```

## 测试标记

- `@pytest.mark.slow`: 标记为慢速测试
- `@pytest.mark.integration`: 标记为集成测试
- `@pytest.mark.unit`: 标记为单元测试
- `@pytest.mark.asyncio`: 标记为异步测试

## 测试数据

测试使用模拟数据和真实场景数据：

### 模拟数据
- 使用 `unittest.mock` 模拟外部依赖
- 模拟Redis连接和操作
- 模拟异常情况

### 真实场景
- 用户会话缓存
- 产品目录缓存
- API响应缓存
- 系统配置缓存

## 性能测试

包含以下性能测试：

### 缓存性能
- 大量缓存操作（1000次）
- 并发操作（100个并发）
- 内存使用监控

### 装饰器性能
- 缓存命中vs未命中性能对比
- 并发装饰器调用
- 序列化性能

## 错误处理测试

测试各种错误情况：

### 存储错误
- Redis连接失败
- 存储操作异常
- 网络超时

### 装饰器错误
- 函数执行异常
- 参数错误
- 缓存键生成错误

## 持续集成

测试套件支持CI/CD环境：

### GitHub Actions
```yaml
- name: Run tests
  run: |
    pip install -r requirements-dev.txt
    pytest --cov=fn_cache --cov-report=xml
```

### 本地开发
```bash
# 运行所有测试并生成覆盖率报告
python run_tests.py --coverage

# 检查代码质量
black fn_cache tests
isort fn_cache tests
flake8 fn_cache tests
mypy fn_cache
```

## 测试最佳实践

1. **测试隔离**: 每个测试都是独立的，不依赖其他测试
2. **模拟外部依赖**: 使用mock避免外部服务依赖
3. **异步测试**: 正确使用 `@pytest.mark.asyncio`
4. **性能测试**: 包含合理的性能基准
5. **错误处理**: 测试各种异常情况
6. **真实场景**: 模拟实际使用场景

## 故障排除

### 常见问题

1. **Redis连接错误**: 测试使用mock，不需要真实Redis
2. **异步测试失败**: 确保正确使用 `