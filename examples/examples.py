# 导入 Leo Cache 核心组件
import asyncio
from datetime import datetime

from loguru import logger
from pydantic import BaseModel

from fn_cache import (
    SerializerType,
    cached,
    get_cache_statistics,
)


class City(BaseModel):
    position: tuple[float, float]


class UserInfo(BaseModel):
    name: str
    city: City
    start: datetime


@cached(
    serializer_type=SerializerType.PICKLE,
    key_func=lambda *args: f"u_{args[0] % 4}" if args else "u_0"  # 10个一组
)
async def get_user_info(k: int) -> UserInfo:
    now = datetime.now()
    logger.info(f"初始化用户信息: {now}")
    await asyncio.sleep(1)
    return UserInfo(name=f"u_{k:03d}", city=City(position=(1.2, 4.8)), start=now)


async def main() -> None:
    u_1 = await get_user_info(-1)
    logger.info(f"{u_1=}")
    u_cached = await get_user_info(-1)
    logger.info(f"{u_cached=}")

    import random
    for _ in range(64):
        i = random.randint(1, 64)
        await get_user_info(i)
        
    stat_info = get_cache_statistics()
    logger.info(f"{stat_info=}")


if __name__ == "__main__":
    asyncio.run(main())
