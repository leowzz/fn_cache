.PHONY: help install install-dev test test-cov lint format clean build publish

# 默认目标
help:
	@echo "L-Cache 开发工具"
	@echo ""
	@echo "可用命令:"
	@echo "  install      - 安装基础依赖"
	@echo "  install-dev  - 安装开发依赖"
	@echo "  test         - 运行测试"
	@echo "  test-cov     - 运行测试并生成覆盖率报告"
	@echo "  lint         - 运行代码检查"
	@echo "  format       - 格式化代码"
	@echo "  clean        - 清理构建文件"
	@echo "  build        - 构建分发包"
	@echo "  publish      - 发布到 PyPI (需要配置)"

# 安装基础依赖
install:
	pip install -r requirements.txt

# 安装开发依赖
install-dev:
	pip install -r requirements-dev.txt

# 运行测试
test:
	pytest tests/ -v

# 运行测试并生成覆盖率报告
test-cov:
	pytest tests/ -v --cov=l_cache --cov-report=html --cov-report=term-missing

# 代码检查
lint:
	flake8 l_cache/ tests/
	mypy l_cache/

# 格式化代码
format:
	black l_cache/ tests/
	isort l_cache/ tests/

# 清理构建文件
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# 构建分发包
build: clean
	python -m build

# 发布到 PyPI (需要配置)
publish: build
	twine upload dist/*

# 本地安装开发版本
install-local: clean
	pip install -e .

# 运行示例
example:
	python -m l_cache.examples

# 运行 CLI 工具
cli:
	l-cache --help 