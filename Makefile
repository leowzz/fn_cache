.PHONY: help install install-dev test test-cov lint format clean build publish docs docs-serve docs-clean

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
	@echo "  docs         - 构建文档"
	@echo "  docs-serve   - 启动文档服务器"
	@echo "  docs-clean   - 清理文档构建文件"
	@echo "  docs-install - 安装文档依赖"
	@echo "  docs-build   - 安装依赖并构建文档"
	@echo "  docs-pdf     - 构建 PDF 文档"
	@echo "  docs-script  - 使用脚本构建文档"
	@echo "  docs-script-serve - 使用脚本启动文档服务器"
	@echo "  check        - 运行完整检查 (lint + test)"
	@echo "  dev-setup    - 完整开发环境设置"
	@echo "  version      - 显示版本信息"
	@echo "  example      - 运行示例"
	@echo "  cli          - 运行 CLI 工具"
	@echo "  security-check - 安全检查"
	@echo "  update-deps  - 更新依赖"
	@echo "  quality      - 代码质量检查"
	@echo "  pre-commit   - 预提交检查"
	@echo "  pre-publish  - 发布前检查"

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
	pytest tests/ -v --cov=fn_cache --cov-report=html --cov-report=term-missing

# 代码检查
lint:
	flake8 fn_cache/ tests/
	mypy fn_cache/

# 格式化代码
format:
	black fn_cache/ tests/
	isort fn_cache/ tests/

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

publish-test: build
	twine upload --repository-url https://test.pypi.org/legacy/ dist/* --verbose

# 本地安装开发版本
install-local: clean
	pip install -e .

# 文档相关命令
docs:
	@echo "构建文档..."
	@if [ -f "scripts/build_docs.py" ]; then \
		python scripts/build_docs.py html; \
	else \
		if command -v sphinx-build >/dev/null 2>&1; then \
			cd docs && sphinx-build -b html . _build/html; \
			echo "Sphinx 文档构建完成，访问 docs/_build/html/index.html"; \
		else \
			echo "Sphinx 未安装，使用简单文档服务..."; \
			echo "文档构建完成"; \
		fi; \
	fi

docs-serve: 
	@echo "启动文档服务器..."
	@if [ -d "docs/_build/html" ]; then \
		echo "使用 Sphinx 构建的文档..."; \
		if command -v python3 >/dev/null 2>&1; then \
			python3 -m http.server 8000 --directory docs/_build/html; \
		elif command -v python >/dev/null 2>&1; then \
			python -m http.server 8000 --directory docs/_build/html; \
		else \
			echo "错误: 未找到 Python"; \
			exit 1; \
		fi; \
	else \
		echo "使用简单文档服务..."; \
		if command -v python3 >/dev/null 2>&1; then \
			python3 -m http.server 8000 --directory docs; \
		elif command -v python >/dev/null 2>&1; then \
			python -m http.server 8000 --directory docs; \
		else \
			echo "错误: 未找到 Python"; \
			exit 1; \
		fi; \
	fi

docs-clean:
	@echo "清理文档构建文件..."
	@rm -rf docs/_build/
	@rm -rf docs/.doctrees/
	@rm -rf docs/source/_build/
	@echo "文档清理完成"

docs-install:
	@echo "安装文档依赖..."
	pip install sphinx sphinx-rtd-theme myst-parser

docs-build: docs-install docs
	@echo "文档构建完成"

docs-pdf:
	@echo "构建 PDF 文档..."
	@if [ -f "scripts/build_docs.py" ]; then \
		python scripts/build_docs.py pdf; \
	elif command -v sphinx-build >/dev/null 2>&1; then \
		cd docs && sphinx-build -b latex . _build/latex; \
		cd _build/latex && make; \
		echo "PDF 文档构建完成"; \
	else \
		echo "Sphinx 未安装，无法构建 PDF"; \
	fi

docs-script:
	@echo "使用文档构建脚本..."
	@if [ -f "scripts/build_docs.py" ]; then \
		python scripts/build_docs.py html; \
	else \
		echo "文档构建脚本不存在"; \
	fi

docs-script-serve:
	@echo "使用脚本启动文档服务器..."
	@if [ -f "scripts/build_docs.py" ]; then \
		python scripts/build_docs.py serve --port 8000; \
	else \
		echo "文档构建脚本不存在"; \
	fi

# 完整检查
check: lint test
	@echo "所有检查通过!"

# 开发环境设置
dev-setup: install-dev install-local
	@echo "开发环境设置完成"
	@echo "运行 'make test' 进行测试"
	@echo "运行 'make docs-serve' 查看文档"

# 显示版本信息
version:
	@python -c "import fn_cache; print(f'fn_cache version: {fn_cache.__version__}')"

# 运行示例
example:
	@echo "运行示例..."
	@if [ -d "examples" ]; then \
		python examples/comprehensive_example.py; \
	else \
		echo "示例目录不存在"; \
	fi

# 运行 CLI 工具
cli:
	@echo "CLI 工具帮助信息:"
	fn_cache --help

# 安全检查
security-check:
	@echo "运行安全检查..."
	@if command -v safety >/dev/null 2>&1; then \
		safety check; \
	else \
		echo "safety 未安装，跳过安全检查"; \
	fi

# 依赖更新
update-deps:
	@echo "更新依赖..."
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt
	pip install --upgrade -r requirements-dev.txt

# 代码质量检查
quality: format lint
	@echo "代码质量检查完成"

# 预提交检查
pre-commit: quality test
	@echo "预提交检查通过!"

# 发布前检查
pre-publish: clean quality test-cov security-check
	@echo "发布前检查通过!"