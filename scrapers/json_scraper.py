import asyncio
import logging
import time

import aiohttp

from utils.config import CACHE_SIZE, lock, log_message
from utils.fixed_size_cache import FixedSizeCache
from utils.global_storage import GlobalCache

url = 'https://www.prnewswire.com/bin/prnewswire/prnTypeaheadService/?keyword=&sitekey=prnewswire&pagePath=/content/prnewswire/'
cache = GlobalCache(CACHE_SIZE)
local_cache = FixedSizeCache(CACHE_SIZE)


async def get_data():
    async with aiohttp.ClientSession() as session:
        while True:
            request_started = time.time()
            async with session.get(url) as response:
                request_finished = time.time()
                response.raise_for_status()
                response_json = await response.json()
                for news in response_json['result']['release']['hits'][:CACHE_SIZE]:
                    guid = news['_source']['url'][0]
                    if await local_cache.contains(guid):
                        break
                    else:
                        async with lock:
                            if not await cache.contains(guid):
                                log_message(f"JSON | NEW | {guid}, request started at {request_started}, "
                                            f"execution time {request_finished - request_started}".strip())
                                await cache.add(guid)
                                await local_cache.add(guid)
                                continue
                            await local_cache.add(guid)
                            log_message(
                                f"JSON | EXISTED | {guid}, request started at {request_started}, "
                                f"execution time {request_finished - request_started}".strip())


if __name__ == '__main__':
    asyncio.run(get_data())
