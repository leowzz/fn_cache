#!/usr/bin/env python3
"""
测试运行脚本

使用方法:
    python run_tests.py                    # 运行所有测试
    python run_tests.py --unit            # 只运行单元测试
    python run_tests.py --integration     # 只运行集成测试
    python run_tests.py --fast            # 跳过慢速测试
    python run_tests.py --coverage        # 生成覆盖率报告
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """运行命令并处理结果"""
    print(f"\n{'='*60}")
    print(f"运行: {description}")
    print(f"命令: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✅ {description} 成功完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} 失败 (退出码: {e.returncode})")
        return False


def main():
    parser = argparse.ArgumentParser(description='运行L-Cache测试套件')
    parser.add_argument('--unit', action='store_true', help='只运行单元测试')
    parser.add_argument('--integration', action='store_true', help='只运行集成测试')
    parser.add_argument('--fast', action='store_true', help='跳过慢速测试')
    parser.add_argument('--coverage', action='store_true', help='生成覆盖率报告')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--parallel', '-n', type=int, help='并行运行测试的进程数')
    
    args = parser.parse_args()
    
    # 基础pytest命令
    cmd = ['python', '-m', 'pytest']
    
    # 添加参数
    if args.verbose:
        cmd.append('-v')
    
    if args.parallel:
        cmd.extend(['-n', str(args.parallel)])
    
    if args.fast:
        cmd.append('-m')
        cmd.append('not slow')
    
    if args.unit:
        cmd.extend(['tests/test_manager.py', 'tests/test_storages.py', 'tests/test_decorators.py', 'tests/test_utils.py'])
    elif args.integration:
        cmd.extend(['tests/test_integration.py'])
    else:
        # 运行所有测试
        cmd.append('tests/')
    
    # 运行测试
    success = run_command(cmd, '测试套件')
    
    # 如果测试成功且请求覆盖率报告
    if success and args.coverage:
        print("\n生成覆盖率报告...")
        coverage_cmd = ['python', '-m', 'coverage', 'html']
        run_command(coverage_cmd, '覆盖率报告生成')
        
        # 显示覆盖率摘要
        summary_cmd = ['python', '-m', 'coverage', 'report']
        run_command(summary_cmd, '覆盖率摘要')
    
    if success:
        print("\n🎉 所有测试通过!")
        sys.exit(0)
    else:
        print("\n💥 测试失败!")
        sys.exit(1)


if __name__ == '__main__':
    main() 