# 开发环境

本文档介绍如何设置 fn_cache 的开发环境。

## 🚀 快速设置

### 一键设置开发环境

```bash
make dev-setup
```

这个命令会自动：
1. 安装开发依赖
2. 安装本地开发版本
3. 显示后续步骤

### 手动设置

```bash
# 1. 克隆仓库
git clone https://github.com/leowzz/fn_cache.git
cd fn_cache

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 3. 安装开发依赖
make install-dev

# 4. 安装本地开发版本
make install-local
```

## 🛠️ 开发工具

### Makefile 命令

fn_cache 提供了丰富的 Makefile 命令来简化开发工作：

#### 基础命令

```bash
make help          # 显示所有可用命令
make install       # 安装基础依赖
make install-dev   # 安装开发依赖
make version       # 显示版本信息
```

#### 代码质量

```bash
make format        # 格式化代码 (black + isort)
make lint          # 代码检查 (flake8 + mypy)
make quality       # 代码质量检查 (format + lint)
```

#### 测试

```bash
make test          # 运行测试
make test-cov      # 运行测试并生成覆盖率报告
```

#### 文档

```bash
make docs          # 构建文档
make docs-serve    # 启动文档服务器 (http://localhost:8000)
make docs-clean    # 清理文档构建文件
make docs-install  # 安装文档依赖
make docs-build    # 安装依赖并构建文档
make docs-pdf      # 构建 PDF 文档
```

#### 构建和发布

```bash
make build         # 构建分发包
make publish       # 发布到 PyPI
make publish-test  # 发布到 Test PyPI
```

#### 检查和验证

```bash
make check         # 完整检查 (lint + test)
make pre-commit    # 预提交检查 (quality + test)
make pre-publish   # 发布前检查 (clean + quality + test-cov + security-check)
make security-check # 安全检查
```

#### 维护

```bash
make clean         # 清理构建文件
make update-deps   # 更新依赖
```

#### 示例和工具

```bash
make example       # 运行示例
make cli           # 运行 CLI 工具
```

## 🔧 开发工作流

### 日常开发

```bash
# 1. 开始新功能开发
git checkout -b feature/new-feature

# 2. 编写代码
# ... 编辑代码 ...

# 3. 代码质量检查
make quality

# 4. 运行测试
make test

# 5. 提交代码
git add .
git commit -m "feat: add new feature"

# 6. 推送代码
git push origin feature/new-feature
```

### 发布前检查

```bash
# 运行完整的发布前检查
make pre-publish
```

这个命令会：
1. 清理构建文件
2. 格式化代码
3. 运行代码检查
4. 运行测试并生成覆盖率报告
5. 运行安全检查

### 文档开发

```bash
# 1. 安装文档依赖
make docs-install

# 2. 构建文档
make docs

# 3. 启动文档服务器
make docs-serve

# 4. 在浏览器中访问 http://localhost:8000
```

## 📋 代码规范

### Python 代码规范

fn_cache 使用以下工具确保代码质量：

- **Black**: 代码格式化
- **isort**: 导入排序
- **flake8**: 代码检查
- **mypy**: 类型检查

### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建过程或辅助工具的变动
```

### 分支命名规范

- `feature/功能名称` - 新功能开发
- `fix/问题描述` - Bug 修复
- `docs/文档更新` - 文档更新
- `refactor/重构描述` - 代码重构

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
make test

# 运行测试并生成覆盖率报告
make test-cov

# 运行特定测试文件
pytest tests/test_decorators.py -v

# 运行特定测试函数
pytest tests/test_decorators.py::test_basic_caching -v
```

### 测试覆盖率

测试覆盖率报告会生成在 `htmlcov/` 目录中，可以通过浏览器查看：

```bash
# 生成覆盖率报告后
open htmlcov/index.html  # macOS
# 或
xdg-open htmlcov/index.html  # Linux
# 或手动打开 htmlcov/index.html
```

## 📚 文档开发

### 文档结构

```
docs/
├── README.md                    # 文档主页
├── installation.md              # 安装指南
├── quickstart.md                # 快速上手
├── faq.md                       # 常见问题
├── concepts/                    # 核心概念
├── api/                         # API 参考
├── examples/                    # 示例教程
├── conf.py                      # Sphinx 配置
├── index.rst                    # Sphinx 索引
└── _static/                     # 静态文件
```

### 添加新文档

1. 在相应目录创建 `.md` 文件
2. 在 `docs/index.rst` 中添加链接
3. 运行 `make docs` 构建文档
4. 运行 `make docs-serve` 预览

### 文档格式

- 使用 Markdown 格式
- 遵循 reST 风格的文档字符串
- 包含代码示例
- 添加适当的标题和链接

## 🔍 调试

### 日志配置

fn_cache 使用 loguru 进行日志记录：

```python
from loguru import logger

# 设置日志级别
logger.add("debug.log", level="DEBUG")

# 在代码中使用
logger.debug("调试信息")
logger.info("信息")
logger.warning("警告")
logger.error("错误")
```

### 调试模式

```bash
# 设置环境变量启用调试
export FN_CACHE_DEBUG=1

# 或在代码中设置
import os
os.environ["FN_CACHE_DEBUG"] = "1"
```

## 🚀 性能分析

### 性能测试

```bash
# 运行性能测试
python -m pytest tests/test_performance.py -v

# 使用 cProfile 分析性能
python -m cProfile -o profile.stats examples/comprehensive_example.py
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(10)"
```

### 内存分析

```bash
# 使用 memory_profiler 分析内存
pip install memory_profiler
python -m memory_profiler examples/memory_monitoring_example.py
```

## 🔧 环境变量

### 开发环境变量

```bash
# 调试模式
export FN_CACHE_DEBUG=1

# Redis 配置
export FN_CACHE_REDIS_HOST=localhost
export FN_CACHE_REDIS_PORT=6379
export FN_CACHE_REDIS_DB=0

# 默认缓存配置
export FN_CACHE_DEFAULT_TTL=600
export FN_CACHE_DEFAULT_MAX_SIZE=1000

# 测试配置
export FN_CACHE_TEST_MODE=1
```

## 📦 发布流程

### 版本管理

1. 更新 `fn_cache/__init__.py` 中的版本号
2. 更新 `docs/conf.py` 中的版本号
3. 更新 `CHANGELOG.md`

### 发布步骤

```bash
# 1. 运行发布前检查
make pre-publish

# 2. 构建分发包
make build

# 3. 测试发布
make publish-test

# 4. 正式发布
make publish
```

### 发布检查清单

- [ ] 所有测试通过
- [ ] 代码覆盖率达标
- [ ] 文档更新完整
- [ ] 版本号正确
- [ ] CHANGELOG 更新
- [ ] 依赖版本检查

## 🤝 贡献指南

### 提交 Pull Request

1. Fork 项目
2. 创建功能分支
3. 编写代码和测试
4. 运行完整检查：`make pre-commit`
5. 提交 Pull Request

### 代码审查

- 确保代码符合项目规范
- 添加适当的测试
- 更新相关文档
- 提供清晰的提交信息

## 📞 获取帮助

如果在开发过程中遇到问题：

1. 查看 [常见问题](faq.md)
2. 搜索 [GitHub Issues](https://github.com/leowzz/fn_cache/issues)
3. 提交新的 Issue
4. 查看 [API 文档](../api/decorators.md)

## 🔗 相关链接

- [项目主页](https://github.com/leowzz/fn_cache)
- [PyPI 包](https://pypi.org/project/fn-cache/)
- [问题反馈](https://github.com/leowzz/fn_cache/issues)
- [贡献指南](contributing.md) 