#!/usr/bin/env python3
"""
L-Cache: 轻量级通用缓存库

这是一个支持多种存储后端（内存、Redis）和缓存策略（LRU、TTL）的通用缓存库。
提供同步和异步API，支持函数装饰器和直接调用方式。
"""

from setuptools import setup, find_packages
import os

# 读取 README 文件
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# 读取版本信息
def get_version():
    with open("fn_cache/__init__.py", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"\'')
    return "1.0.0"

setup(
    name="fn_cache",
    version=get_version(),
    author="WangZhanze",
    author_email="leolswq@163.com",
    description="轻量级通用缓存库",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/leowzz/fn_cache",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
        "Topic :: Database :: Database Engines/Servers",
    ],
    python_requires=">=3.8",
    install_requires=[
        "redis>=4.0.0",
        "typing-extensions>=4.0.0;python_version<'3.9'",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=1.0.0",
        ],
    },
    keywords="cache, redis, memory, ttl, lru, async, decorator",
    project_urls={
        "Bug Reports": "https://github.com/leowzz/fn_cache/issues",
        "Source": "https://github.com/leowzz/fn_cache",
        "Documentation": "https://fn_cache.readthedocs.io/",
    },
    include_package_data=True,
    zip_safe=False,
) 