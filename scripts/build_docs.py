#!/usr/bin/env python3
"""
fn_cache 文档构建脚本

支持多种文档格式的构建：
- HTML (Sphinx)
- PDF (LaTeX)
- 简单 Markdown 服务
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """运行命令并处理错误"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {cmd}")
        print(f"错误输出: {e.stderr}")
        if check:
            sys.exit(1)
        return e


def check_sphinx():
    """检查 Sphinx 是否已安装"""
    try:
        subprocess.run(["sphinx-build", "--version"], 
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_sphinx():
    """安装 Sphinx 和相关依赖"""
    print("安装 Sphinx 和相关依赖...")
    run_command("pip install sphinx sphinx-rtd-theme myst-parser")


def build_html_docs():
    """构建 HTML 文档"""
    docs_dir = Path("docs")
    if not docs_dir.exists():
        print("错误: docs 目录不存在")
        return False
    
    # 检查是否有 Sphinx 配置
    conf_file = docs_dir / "conf.py"
    if not conf_file.exists():
        print("警告: 未找到 Sphinx 配置文件，使用简单文档服务")
        return False
    
    # 检查 Sphinx 是否安装
    if not check_sphinx():
        print("Sphinx 未安装，正在安装...")
        install_sphinx()
    
    # 构建 HTML 文档
    print("构建 HTML 文档...")
    build_dir = docs_dir / "_build" / "html"
    build_dir.mkdir(parents=True, exist_ok=True)
    
    # 使用当前目录作为源目录，而不是期望 source 子目录
    result = run_command(
        "sphinx-build -b html . _build/html",
        cwd=docs_dir,
        check=False
    )
    
    if result.returncode == 0:
        print(f"HTML 文档构建完成: {build_dir.absolute()}")
        return True
    else:
        print("HTML 文档构建失败")
        return False


def build_pdf_docs():
    """构建 PDF 文档"""
    docs_dir = Path("docs")
    if not docs_dir.exists():
        print("错误: docs 目录不存在")
        return False
    
    # 检查 Sphinx 是否安装
    if not check_sphinx():
        print("Sphinx 未安装，无法构建 PDF")
        return False
    
    # 检查 LaTeX 是否可用
    try:
        subprocess.run(["pdflatex", "--version"], 
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("警告: pdflatex 未安装，无法构建 PDF")
        return False
    
    # 构建 PDF 文档
    print("构建 PDF 文档...")
    build_dir = docs_dir / "_build" / "latex"
    build_dir.mkdir(parents=True, exist_ok=True)
    
    # 构建 LaTeX
    result = run_command(
        "sphinx-build -b latex . _build/latex",
        cwd=docs_dir,
        check=False
    )
    
    if result.returncode != 0:
        print("LaTeX 构建失败")
        return False
    
    # 生成 PDF
    result = run_command(
        "make",
        cwd=build_dir,
        check=False
    )
    
    if result.returncode == 0:
        pdf_file = build_dir / "fn_cache.pdf"
        if pdf_file.exists():
            print(f"PDF 文档构建完成: {pdf_file.absolute()}")
            return True
    
    print("PDF 文档构建失败")
    return False


def serve_docs(port=8000):
    """启动文档服务器"""
    docs_dir = Path("docs")
    
    # 检查是否有构建的 HTML 文档
    html_dir = docs_dir / "_build" / "html"
    if html_dir.exists() and (html_dir / "index.html").exists():
        print(f"启动 Sphinx HTML 文档服务器 (端口: {port})...")
        serve_dir = html_dir
    else:
        print(f"启动简单文档服务器 (端口: {port})...")
        serve_dir = docs_dir
    
    print(f"文档服务器地址: http://localhost:{port}")
    print("按 Ctrl+C 停止服务器")
    
    try:
        subprocess.run([
            sys.executable, "-m", "http.server", str(port), 
            "--directory", str(serve_dir)
        ])
    except KeyboardInterrupt:
        print("\n文档服务器已停止")


def clean_docs():
    """清理文档构建文件"""
    docs_dir = Path("docs")
    if not docs_dir.exists():
        print("docs 目录不存在")
        return
    
    build_dirs = [
        docs_dir / "_build",
        docs_dir / ".doctrees"
    ]
    
    for build_dir in build_dirs:
        if build_dir.exists():
            import shutil
            shutil.rmtree(build_dir)
            print(f"已清理: {build_dir}")
    
    print("文档清理完成")


def main():
    parser = argparse.ArgumentParser(description="fn_cache 文档构建工具")
    parser.add_argument(
        "action",
        choices=["html", "pdf", "serve", "clean", "install"],
        help="要执行的操作"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="文档服务器端口 (默认: 8000)"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="强制重新安装依赖"
    )
    
    args = parser.parse_args()
    
    if args.action == "install":
        install_sphinx()
    elif args.action == "html":
        build_html_docs()
    elif args.action == "pdf":
        build_pdf_docs()
    elif args.action == "serve":
        serve_docs(args.port)
    elif args.action == "clean":
        clean_docs()


if __name__ == "__main__":
    main() 