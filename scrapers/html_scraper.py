import asyncio
import logging
import time

import aiohttp
from bs4 import BeautifulSoup

from utils.fixed_size_cache import FixedSizeCache
from utils.global_storage import GlobalCache
from utils.config import CACHE_SIZE, lock, log_message

url = 'https://www.prnewswire.com/news-releases/news-releases-list/'
cache = GlobalCache(CACHE_SIZE)
local_cache = FixedSizeCache(CACHE_SIZE)


async def check_if_new_news_appears(html, request_started, request_finished):
    soup = BeautifulSoup(html, 'lxml')
    news_links = soup.find_all('a', class_='newsreleaseconsolidatelink')

    for link in news_links[:CACHE_SIZE]:
        guid = link['href'].split("/")[-1].replace(".html", "")
        if await local_cache.contains(guid):
            break
        else:
            async with lock:
                if not await cache.contains(guid):
                    log_message(f"HTML | NEW | {guid} | started at {request_started} | "
                                f"execution time {request_finished - request_started}".strip())
                    await cache.add(guid)
                    await local_cache.add(guid)
                    continue
                await local_cache.add(guid)
                log_message(
                    f"HTML | EXISTED | {guid} | request started at {request_started} | "
                    f"execution time {request_finished - request_started}".strip())


async def get_data():
    async with aiohttp.ClientSession() as session:
        while True:
            request_started = time.time()
            async with session.get(url) as response:
                request_finished = time.time()
                await check_if_new_news_appears(await response.text(), request_started, request_finished)


if __name__ == '__main__':
    asyncio.run(get_data())
