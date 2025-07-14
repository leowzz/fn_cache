#!/usr/bin/env python3
"""
展示新的缓存模式示例

这个示例展示了重构后的缓存装饰器的使用方法：
1. 简化的参数配置
2. 自定义缓存键生成器
3. 通过装饰后的函数访问缓存管理器
"""

import asyncio
import time
import sys
import os

from fn_cache import cached


def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    @cached(ttl_seconds=60)
    def get_user_info(user_id: int):
        print(f"从数据库获取用户 {user_id} 的信息")
        return {"user_id": user_id, "name": f"User{user_id}", "email": f"user{user_id}@example.com"}
    
    # 第一次调用
    result1 = get_user_info(123)
    print(f"结果: {result1}")
    
    # 第二次调用（从缓存返回）
    result2 = get_user_info(123)
    print(f"结果: {result2}")
    
    # 通过装饰后的函数访问缓存管理器
    print(f"缓存管理器: {get_user_info.cache}")
    print(f"缓存配置: {get_user_info.cache.config}")
    
    # 清除缓存
    get_user_info.cache.clear_sync()
    print("已清除缓存")
    
    # 再次调用（重新执行）
    result3 = get_user_info(123)
    print(f"清除缓存后结果: {result3}")
    print()


def example_custom_key_func():
    """自定义缓存键生成器示例"""
    print("=== 自定义缓存键生成器示例 ===")
    
    def custom_key_func(*args, **kwargs):
        # 只使用第一个参数作为缓存键的一部分
        user_id = args[0] if args else kwargs.get('user_id', 'unknown')
        # 添加环境标识
        environment = "prod"  # 可以从环境变量获取
        return f"user:{environment}:{user_id}"
    
    @cached(key_func=custom_key_func, ttl_seconds=300)
    def get_user_profile(user_id: int, include_sensitive: bool = False):
        print(f"获取用户 {user_id} 的详细资料")
        return {
            "user_id": user_id,
            "name": f"User{user_id}",
            "profile": f"Profile for user {user_id}",
            "sensitive_data": "secret" if include_sensitive else None
        }
    
    # 调用函数
    result1 = get_user_profile(123)
    print(f"结果: {result1}")
    
    # 相同用户ID，不同参数（应该从缓存返回，因为key_func只使用user_id）
    result2 = get_user_profile(123, include_sensitive=True)
    print(f"结果: {result2}")
    
    # 不同用户ID（应该重新执行）
    result3 = get_user_profile(456)
    print(f"结果: {result3}")
    print()


async def example_async_usage():
    """异步使用示例"""
    print("=== 异步使用示例 ===")
    
    @cached(ttl_seconds=60)
    async def fetch_api_data(endpoint: str, params: dict):
        print(f"从API获取数据: {endpoint}")
        await asyncio.sleep(0.1)  # 模拟网络请求
        return {
            "endpoint": endpoint,
            "params": params,
            "data": f"Data from {endpoint}",
            "timestamp": time.time()
        }
    
    # 第一次调用
    result1 = await fetch_api_data("/users", {"page": 1})
    print(f"结果: {result1}")
    
    # 第二次调用（从缓存返回）
    result2 = await fetch_api_data("/users", {"page": 1})
    print(f"结果: {result2}")
    
    # 通过装饰后的函数访问缓存管理器
    print(f"缓存管理器: {fetch_api_data.cache}")
    
    # 清除缓存
    await fetch_api_data.cache.clear()
    print("已清除缓存")
    
    # 再次调用（重新执行）
    result3 = await fetch_api_data("/users", {"page": 1})
    print(f"清除缓存后结果: {result3}")
    print()


def example_dynamic_ttl():
    """动态TTL示例"""
    print("=== 动态TTL示例 ===")
    
    def make_expire_sec_func(result: dict) -> int:
        # 根据用户类型动态设置过期时间
        user_type = result.get("user_type", "normal")
        if user_type == "vip":
            return 3600  # VIP用户缓存1小时
        elif user_type == "admin":
            return 1800  # 管理员缓存30分钟
        else:
            return 300   # 普通用户缓存5分钟
    
    @cached(make_expire_sec_func=make_expire_sec_func, ttl_seconds=300)
    def get_user_type(user_id: int):
        print(f"获取用户 {user_id} 的类型")
        # 模拟根据用户ID获取用户类型
        if user_id == 1:
            return {"user_id": user_id, "user_type": "admin"}
        elif user_id == 2:
            return {"user_id": user_id, "user_type": "vip"}
        else:
            return {"user_id": user_id, "user_type": "normal"}
    
    # 获取不同类型用户的信息
    admin_user = get_user_type(1)
    vip_user = get_user_type(2)
    normal_user = get_user_type(3)
    
    print(f"管理员用户: {admin_user}")
    print(f"VIP用户: {vip_user}")
    print(f"普通用户: {normal_user}")
    print()


async def main():
    """主函数"""
    print("开始演示新的缓存模式...\n")
    
    # 基本使用示例
    example_basic_usage()
    
    # 自定义缓存键生成器示例
    example_custom_key_func()
    
    # 异步使用示例
    await example_async_usage()
    
    # 动态TTL示例
    example_dynamic_ttl()
    
    print("演示完成！")


if __name__ == "__main__":
    asyncio.run(main()) 