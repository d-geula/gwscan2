import asyncio
import random


async def human_wait(a: float = 0.6, b: float = 1.2) -> None:
    await asyncio.sleep(random.uniform(a, b))
