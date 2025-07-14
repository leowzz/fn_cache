import asyncio
from typing import Any, Optional, TypeVar, Awaitable, Callable
from loguru import logger
T = TypeVar('T')


def safe_redis_operation(
        operation: Awaitable[T],
        operation_name: str,
        key: str,
        timeout_seconds: float = 1.0,
        default_value: Optional[T] = None,
        suppress_timeout_log: bool = False
) -> Awaitable[Optional[T]]:
    """
    安全的Redis操作包装器

    :param operation: Redis操作
    :param operation_name: 操作名称（用于日志）
    :param key: 操作的键
    :param timeout_seconds: 超时时间
    :param default_value: 超时时的默认值
    :param suppress_timeout_log: 是否抑制超时日志
    :return: 操作结果或默认值
    """

    async def wrapper():
        try:
            return await asyncio.wait_for(operation, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            if not suppress_timeout_log:
                logger.error(f"Redis {operation_name} timeout for key: {key}")
            return default_value
        except Exception as e:
            logger.error(f"Redis {operation_name} error for key {key}: {e}")
            return default_value

    return wrapper()


def safe_redis_void_operation(
        operation: Awaitable[Any],
        operation_name: str,
        key: str,
        timeout_seconds: float = 1.0
) -> Awaitable[None]:
    """
    安全的Redis无返回值操作包装器

    :param operation: Redis操作
    :param operation_name: 操作名称（用于日志）
    :param key: 操作的键
    :param timeout_seconds: 超时时间
    """

    async def wrapper():
        try:
            await asyncio.wait_for(operation, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            logger.error(f"Redis {operation_name} timeout for key: {key}")
        except Exception as e:
            logger.error(f"Redis {operation_name} error for key {key}: {e}")

    return wrapper()


def safe_cache_operation(
        operation: Callable[[], T],
        operation_name: str,
        default_value: Optional[T] = None
) -> Optional[T]:
    """
    安全的缓存操作包装器（同步版本）

    :param operation: 缓存操作函数
    :param operation_name: 操作名称（用于日志）
    :param default_value: 出错时的默认值
    :return: 操作结果或默认值
    """
    try:
        return operation()
    except Exception as e:
        logger.error(f"Cache {operation_name} error: {e}")
        return default_value


async def safe_async_cache_operation(
        operation: Callable[[], Awaitable[T]],
        operation_name: str,
        default_value: Optional[T] = None
) -> Optional[T]:
    """
    安全的缓存操作包装器（异步版本）

    :param operation: 异步缓存操作函数
    :param operation_name: 操作名称（用于日志）
    :param default_value: 出错时的默认值
    :return: 操作结果或默认值
    """
    try:
        return await operation()
    except Exception as e:
        logger.error(f"Cache {operation_name} error: {e}")
        return default_value
