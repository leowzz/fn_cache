#!/usr/bin/env python3
"""
Leo Cache 示例运行器

快速运行各种示例，展示 Leo Cache 的功能特性。
"""

import sys
import os
import subprocess
import asyncio
from pathlib import Path


def print_banner():
    """打印欢迎横幅"""
    print("🚀 Leo Cache 示例运行器")
    print("=" * 50)
    print("选择要运行的示例：")
    print()


def list_examples():
    """列出可用的示例"""
    examples_dir = Path("examples")
    examples = []
    
    for file in examples_dir.glob("*.py"):
        if file.name != "__init__.py":
            examples.append(file)
    
    return sorted(examples)


def run_example(example_path: Path):
    """运行指定的示例"""
    print(f"正在运行示例: {example_path.name}")
    print("-" * 30)
    
    try:
        # 切换到项目根目录
        os.chdir(Path(__file__).parent)
        
        # 运行示例
        result = subprocess.run(
            [sys.executable, str(example_path)],
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print(f"\n✅ 示例 {example_path.name} 运行成功！")
        else:
            print(f"\n❌ 示例 {example_path.name} 运行失败！")
            print(f"错误代码: {result.returncode}")
            
    except Exception as e:
        print(f"\n❌ 运行示例时出现错误: {e}")


def check_dependencies():
    """检查依赖是否满足"""
    print("🔍 检查依赖...")
    
    # 检查基本依赖
    try:
        import fn_cache
        print("✅ Leo Cache 库已安装")
    except ImportError:
        print("❌ Leo Cache 库未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
        print("✅ Leo Cache 库安装完成")
    
    # 检查可选依赖
    try:
        import msgpack
        print("✅ MessagePack 已安装")
    except ImportError:
        print("⚠️  MessagePack 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "msgpack"], check=True)
        print("✅ MessagePack 安装完成")
    
    print()


def main():
    """主函数"""
    print_banner()
    
    # 检查依赖
    check_dependencies()
    
    # 列出示例
    examples = list_examples()
    
    if not examples:
        print("❌ 未找到示例文件")
        return
    
    print("可用的示例：")
    for i, example in enumerate(examples, 1):
        print(f"  {i}. {example.stem}")
    
    print()
    print("特殊选项：")
    print(f"  {len(examples) + 1}. 运行所有示例")
    print(f"  {len(examples) + 2}. 退出")
    print()
    
    while True:
        try:
            choice = input("请选择要运行的示例 (输入数字): ").strip()
            
            if not choice:
                continue
            
            choice_num = int(choice)
            
            if choice_num == len(examples) + 1:
                # 运行所有示例
                print("\n🔄 运行所有示例...")
                for example in examples:
                    print(f"\n{'='*60}")
                    run_example(example)
                    print(f"{'='*60}")
                break
                
            elif choice_num == len(examples) + 2:
                # 退出
                print("👋 再见！")
                break
                
            elif 1 <= choice_num <= len(examples):
                # 运行指定示例
                selected_example = examples[choice_num - 1]
                run_example(selected_example)
                break
                
            else:
                print("❌ 无效的选择，请重新输入")
                
        except ValueError:
            print("❌ 请输入有效的数字")
        except KeyboardInterrupt:
            print("\n👋 用户取消操作")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")
            break


if __name__ == "__main__":
    main() 