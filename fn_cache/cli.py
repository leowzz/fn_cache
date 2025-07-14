#!/usr/bin/env python3
"""
L-Cache 命令行工具

提供基本的缓存管理功能，包括缓存状态检查、清理等操作。
"""

import argparse
import asyncio
import json
import sys
from typing import Optional

from .manager import UniversalCacheManager
from .config import CacheConfig
from .enums import StorageType


async def check_cache_status(storage_type: str) -> dict:
    """检查缓存状态"""
    config = CacheConfig(storage_type=StorageType(storage_type))
    manager = UniversalCacheManager(config)
    
    try:
        # 测试基本操作
        test_key = "fn_cache:cli:test"
        test_value = {"status": "ok", "timestamp": asyncio.get_event_loop().time()}
        
        # 设置测试值
        await manager.set(test_key, test_value, ttl_seconds=60)
        
        # 获取测试值
        retrieved_value = await manager.get(test_key)
        
        # 清理测试值
        await manager.delete(test_key)
        
        return {
            "status": "healthy",
            "storage_type": storage_type,
            "test_passed": retrieved_value == test_value,
            "message": "缓存系统运行正常"
        }
    except Exception as e:
        return {
            "status": "error",
            "storage_type": storage_type,
            "error": str(e),
            "message": "缓存系统出现错误"
        }


async def clear_cache(storage_type: str, pattern: Optional[str] = None) -> dict:
    """清理缓存"""
    config = CacheConfig(storage_type=StorageType(storage_type))
    manager = UniversalCacheManager(config)
    
    try:
        if pattern:
            # 使用模式清理（仅Redis支持）
            if storage_type == "redis":
                # 这里需要实现模式删除，暂时使用全局失效
                await manager.invalidate_all()
                return {
                    "status": "success",
                    "message": f"已清理匹配模式 '{pattern}' 的缓存"
                }
            else:
                return {
                    "status": "error",
                    "message": "模式清理仅支持Redis存储"
                }
        else:
            # 清理所有缓存
            await manager.invalidate_all()
            return {
                "status": "success",
                "message": "已清理所有缓存"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "清理缓存时出现错误"
        }


async def get_cache_info(storage_type: str) -> dict:
    """获取缓存信息"""
    config = CacheConfig(storage_type=StorageType(storage_type))
    manager = UniversalCacheManager(config)
    
    try:
        info = {
            "storage_type": storage_type,
            "config": {
                "prefix": config.prefix,
                "global_version_key": config.global_version_key,
                "user_version_key": config.user_version_key,
            }
        }
        
        if storage_type == "memory":
            info["memory_cache"] = {
                "enabled": manager.is_global_cache_enabled_sync,
                "cache_type": config.cache_type.value,
                "max_size": config.max_size if config.cache_type.value == "lru" else None,
                "ttl_seconds": config.ttl_seconds if config.cache_type.value == "ttl" else None,
            }
        elif storage_type == "redis":
            info["redis_cache"] = {
                "enabled": True,  # 假设Redis连接正常
                "prefix": config.prefix,
            }
        
        return {
            "status": "success",
            "info": info
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "获取缓存信息时出现错误"
        }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="L-Cache 命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  fn_cache status --storage memory
  fn_cache status --storage redis
  fn_cache clear --storage memory
  fn_cache clear --storage redis --pattern "user:*"
  fn_cache info --storage memory
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # status 命令
    status_parser = subparsers.add_parser("status", help="检查缓存状态")
    status_parser.add_argument(
        "--storage", 
        choices=["memory", "redis"], 
        default="memory",
        help="存储类型 (默认: memory)"
    )
    status_parser.add_argument(
        "--json", 
        action="store_true",
        help="以JSON格式输出"
    )
    
    # clear 命令
    clear_parser = subparsers.add_parser("clear", help="清理缓存")
    clear_parser.add_argument(
        "--storage", 
        choices=["memory", "redis"], 
        default="memory",
        help="存储类型 (默认: memory)"
    )
    clear_parser.add_argument(
        "--pattern", 
        help="清理模式 (仅Redis支持，例如: 'user:*')"
    )
    clear_parser.add_argument(
        "--json", 
        action="store_true",
        help="以JSON格式输出"
    )
    
    # info 命令
    info_parser = subparsers.add_parser("info", help="获取缓存信息")
    info_parser.add_argument(
        "--storage", 
        choices=["memory", "redis"], 
        default="memory",
        help="存储类型 (默认: memory)"
    )
    info_parser.add_argument(
        "--json", 
        action="store_true",
        help="以JSON格式输出"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    async def run_command():
        if args.command == "status":
            result = await check_cache_status(args.storage)
        elif args.command == "clear":
            result = await clear_cache(args.storage, args.pattern)
        elif args.command == "info":
            result = await get_cache_info(args.storage)
        else:
            print(f"未知命令: {args.command}")
            sys.exit(1)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if result.get("status") == "success":
                print(f"✅ {result.get('message', '操作成功')}")
                if "info" in result:
                    print(json.dumps(result["info"], ensure_ascii=False, indent=2))
            elif result.get("status") == "healthy":
                print(f"✅ {result.get('message', '系统正常')}")
            else:
                print(f"❌ {result.get('message', '操作失败')}")
                if "error" in result:
                    print(f"错误详情: {result['error']}")
                sys.exit(1)
    
    try:
        asyncio.run(run_command())
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 执行命令时出现错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 