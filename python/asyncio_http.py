#!/usr/bin/env python3

import asyncio
from aiohttp import ClientConnectorError, ClientSession


async def fetch(semaphore, session, url):
    try:
        async with semaphore, session.get(url) as response:
            print(f'Received {response.status} status from {response.url}')
            return await response.text()
            #return await response.json()
            #return await response.read()
    except ClientConnectorError:
        return f'Could not connect to {url}'


async def main(num_requests, batch_size):
    url = 'http://localhost:8080/{}'
    semaphore = asyncio.Semaphore(batch_size)
    async with ClientSession() as session:
        tasks = [asyncio.ensure_future(fetch(semaphore, session, url.format(n + 1)))
                 for n in range(num_requests)]
        results = await asyncio.gather(*tasks)
    print('\n'.join(str(r) for r in results))


loop = asyncio.get_event_loop()
loop.run_until_complete(main(10, 2))
loop.close()

# python 3.7+
#asyncio.run(main(10, 2))
