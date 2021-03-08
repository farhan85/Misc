#!/usr/bin/env python3

import asyncio
import random
import time


def make_async(func):
    async def f(*args):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)
    return f


@make_async
def blocking_task(id):
    print(f"{id} - begin")
    time.sleep(random.randint(1, 5))
    print(f"{id} - end")


async def async_task(id):
    print(f"{id} - begin")
    await asyncio.sleep(1)
    print(f"{id} - end")


async def main():
    #tasks = [asyncio.ensure_future(async_task(i)) for i in range(10)]
    tasks = [asyncio.ensure_future(blocking_task(i)) for i in range(10)]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    s = time.perf_counter()
    # asyncio.run(main()) # Python3.7
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")
