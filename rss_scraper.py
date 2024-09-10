import logging
import time
from concurrent.futures.thread import ThreadPoolExecutor
from bs4 import BeautifulSoup
import aiohttp
import asyncio
from async_logger import get_async_logger

rss_url = 'https://www.prnewswire.com/rss/news-releases-list.rss'


async def get_start_etag_and_guid():
    async with aiohttp.ClientSession() as session:
        async with session.get(rss_url) as response:
            soup = BeautifulSoup(await response.text(), 'xml')
            guid = soup.find('guid').text
            return response.headers['Etag'], guid


current_etag, current_guid = None, None
executor = ThreadPoolExecutor()
lock = asyncio.Lock()


async def check_if_new_news_appears(html, start_time: time.time, end_time: time.time):
    soup = BeautifulSoup(html, 'xml')
    guid = soup.find('guid').text
    global current_guid
    if guid != current_guid:
        async def clear_pool_executor():
            async with lock:
                global executor
                executor.shutdown(wait=True)
                executor = ThreadPoolExecutor()

        async with await get_async_logger() as logger:
            await logger.log(logging.INFO,
                             f'NEW NEWS in rss, session started at {start_time}, session finished at {end_time}')
            await logger.log(logging.INFO, f'new news guid is {guid}')

        async with lock:
            current_guid = guid

        global current_etag
        async with await get_async_logger() as logger:
            await logger.log(logging.INFO, f'current etag is {current_etag}, current guid is {current_guid}')

        await clear_pool_executor()
    else:
        async with await get_async_logger() as logger:
            await logger.log(logging.INFO, f'NEWS UPDATE in rss {start_time}, session finished at {end_time}')


async def get_rss_data():
    global current_etag, current_guid
    current_etag, current_guid = await get_start_etag_and_guid()
    # current_guid = 'https://www.prnewswire.com/news-releases/metaverseme-set-to-transform-web3-gaming-via-the-hedera-evm-partnering-with-thirdweb-and-the-hbar-foundation-302243926.html'
    # current_etag = 'W/"9e3d-621c872faa36c"'
    async with await get_async_logger() as logger:
        await logger.log(logging.INFO, f'started Etag is {current_etag}, started guid is {current_guid}')

    async with aiohttp.ClientSession() as session:
        start_session_time = time.time()
        while True:
            headers = {
                "if-none-match": str(current_etag)
            }
            async with session.get(rss_url, headers=headers) as response:
                if response.status == 304:  # NOQA
                    continue
                else:
                    finish_session_time = time.time()
                    async with await get_async_logger() as logger:
                        # await logger.log(logging.INFO, f'page was modified, new Etag is {response.headers['Etag']}')
                        async with lock:
                            current_etag = response.headers['Etag']
                        await check_if_new_news_appears(await response.text(), start_session_time, finish_session_time)


if __name__ == '__main__':
    # asyncio.run(test_log())
    asyncio.run(get_rss_data())
