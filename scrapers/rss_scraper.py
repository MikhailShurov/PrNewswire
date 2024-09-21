import logging
import time

from bs4 import BeautifulSoup
import aiohttp
import asyncio
from utils.fixed_size_cache import FixedSizeCache
from utils.config import CACHE_SIZE, lock, log_message
from utils.global_storage import GlobalCache

cache = GlobalCache(CACHE_SIZE)
local_cache = FixedSizeCache(CACHE_SIZE)
rss_url = 'https://www.prnewswire.com/rss/news-releases-list.rss'
current_etag, current_guid = None, None


async def check_if_new_news_appears(html, request_started, request_finished):
    soup = BeautifulSoup(html, 'xml')
    news_links = soup.find_all('guid')

    for link in news_links[:CACHE_SIZE]:
        guid = link.text.split("/")[-1].replace(".html", "")
        if await local_cache.contains(guid):
            break
        else:
            async with lock:
                if not await cache.contains(guid):
                    log_message(f"RSS | NEW | {guid}, request started at {request_started}, "
                                f"execution time {request_finished - request_started}".strip())
                    await cache.add(guid)
                    await local_cache.add(guid)
                    continue
                await local_cache.add(guid)
                log_message(
                    f"RSS | EXISTED | {guid}, request started at {request_started}, "
                    f"execution time {request_finished - request_started}".strip())


async def get_data():
    global current_etag
    async with aiohttp.ClientSession() as session:
        while True:
            headers = {
                "if-none-match": str(current_etag)
            }
            request_started = time.time()
            async with session.get(rss_url, headers=headers) as response:
                request_finished = time.time()
                if response.status == 304:
                    continue
                else:
                    async with lock:
                        current_etag = response.headers['Etag']
                    await check_if_new_news_appears(await response.text(), request_started, request_finished)


# ToDo replace with async logger

if __name__ == '__main__':
    asyncio.run(get_data())
