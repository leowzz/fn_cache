# Makefile 使用指南

fn_cache 项目提供了丰富的 Makefile 命令来简化开发工作。

## 🚀 快速开始

### 查看所有可用命令

```bash
make help
```

### 一键设置开发环境

```bash
make dev-setup
```

## 📋 命令分类

### 🔧 基础命令

| 命令 | 描述 |
|------|------|
| `make help` | 显示所有可用命令 |
| `make install` | 安装基础依赖 |
| `make install-dev` | 安装开发依赖 |
| `make version` | 显示版本信息 |

### 🎨 代码质量

| 命令 | 描述 |
|------|------|
| `make format` | 格式化代码 (black + isort) |
| `make lint` | 代码检查 (flake8 + mypy) |
| `make quality` | 代码质量检查 (format + lint) |

### 🧪 测试

| 命令 | 描述 |
|------|------|
| `make test` | 运行测试 |
| `make test-cov` | 运行测试并生成覆盖率报告 |

### 📚 文档

| 命令 | 描述 |
|------|------|
| `make docs` | 构建文档 |
| `make docs-serve` | 启动文档服务器 (http://localhost:8000) |
| `make docs-clean` | 清理文档构建文件 |
| `make docs-install` | 安装文档依赖 |
| `make docs-build` | 安装依赖并构建文档 |
| `make docs-pdf` | 构建 PDF 文档 |
| `make docs-script` | 使用脚本构建文档 |
| `make docs-script-serve` | 使用脚本启动文档服务器 |

### 📦 构建和发布

| 命令 | 描述 |
|------|------|
| `make build` | 构建分发包 |
| `make publish` | 发布到 PyPI |
| `make publish-test` | 发布到 Test PyPI |

### ✅ 检查和验证

| 命令 | 描述 |
|------|------|
| `make check` | 完整检查 (lint + test) |
| `make pre-commit` | 预提交检查 (quality + test) |
| `make pre-publish` | 发布前检查 (clean + quality + test-cov + security-check) |
| `make security-check` | 安全检查 |

### 🛠️ 维护

| 命令 | 描述 |
|------|------|
| `make clean` | 清理构建文件 |
| `make update-deps` | 更新依赖 |

### 🎯 示例和工具

| 命令 | 描述 |
|------|------|
| `make example` | 运行示例 |
| `make cli` | 运行 CLI 工具 |

## 🔄 常用工作流

### 日常开发

```bash
# 1. 设置开发环境
make dev-setup

# 2. 编写代码后，运行质量检查
make quality

# 3. 运行测试
make test

# 4. 提交前检查
make pre-commit
```

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

### 发布前准备

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

## 🎛️ 高级用法

### 组合命令

```bash
# 代码质量 + 测试
make quality test

# 清理 + 构建
make clean build

# 安装依赖 + 构建文档
make docs-install docs
```

### 环境变量

某些命令支持环境变量配置：

```bash
# 设置文档服务器端口
PORT=8080 make docs-serve

# 启用调试模式
FN_CACHE_DEBUG=1 make test
```

### 并行执行

某些命令支持并行执行以提高速度：

```bash
# 并行运行测试
make test -j4

# 并行格式化代码
make format -j4
```

## 🔧 自定义配置

### 添加自定义命令

可以在 Makefile 中添加自定义命令：

```makefile
# 自定义命令示例
custom-command:
	@echo "执行自定义命令..."
	# 你的命令
```

### 修改现有命令

可以修改现有命令的行为：

```makefile
# 修改测试命令
test:
	pytest tests/ -v --tb=short
```

## 🐛 故障排除

### 常见问题

1. **命令未找到**
   ```bash
   # 确保在项目根目录
   pwd
   ls Makefile
   ```

2. **权限问题**
   ```bash
   # 使用 sudo (如果需要)
   sudo make install
   ```

3. **依赖问题**
   ```bash
   # 更新依赖
   make update-deps
   ```

4. **文档构建失败**
   ```bash
   # 清理并重新构建
   make docs-clean
   make docs-install
   make docs
   ```

### 调试模式

启用调试模式以获取更多信息：

```bash
# 显示执行的命令
make -n command

# 显示详细输出
make -d command

# 显示所有信息
make --debug=b command
```

## 📚 相关文档

- [开发环境](docs/development.md) - 详细的开发环境设置
- [贡献指南](docs/contributing.md) - 如何贡献代码
- [测试指南](docs/testing.md) - 测试相关说明

## 🔗 相关链接

- [项目主页](https://github.com/leowzz/fn_cache)
- [Makefile 官方文档](https://www.gnu.org/software/make/)
- [Python Makefile 最佳实践](https://github.com/audreyr/cookiecutter-pypackage) 