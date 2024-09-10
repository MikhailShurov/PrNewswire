import logging
import time
from concurrent.futures.thread import ThreadPoolExecutor
from bs4 import BeautifulSoup
import aiohttp
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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


def log_message(message):
    logging.info(message)


async def check_if_new_news_appears(html, start_time, end_time):
    soup = BeautifulSoup(html, 'xml')
    guid = soup.find('guid').text
    global current_guid
    if guid != current_guid:
        async with lock:
            global executor
            executor.shutdown(wait=True)
            executor = ThreadPoolExecutor()

        log_message(f'NEW NEWS in rss, session started at {start_time}, session finished at {end_time}')
        log_message(f'new news guid is {guid}')

        async with lock:
            current_guid = guid

        global current_etag
        log_message(f'current etag is {current_etag}, current guid is {current_guid}')

    else:
        log_message(f'NEWS UPDATE in rss {start_time}, session finished at {end_time}')


async def get_rss_data():
    global current_etag, current_guid
    current_etag, current_guid = await get_start_etag_and_guid()
    # current_guid = 'https://www.prnewswire.com/news-releases/metaverseme-set-to-transform-web3-gaming-via-the-hedera-evm-partnering-with-thirdweb-and-the-hbar-foundation-302243926.html'
    # current_etag = 'W/"9e3d-621c872faa36c"'
    log_message(f'started Etag is {current_etag}, started guid is {current_guid}')

    async with aiohttp.ClientSession() as session:
        while True:
            start_session_time = time.time()
            headers = {
                "if-none-match": str(current_etag)
            }
            async with session.get(rss_url, headers=headers) as response:
                if response.status == 304:
                    continue
                else:
                    finish_session_time = time.time()
                    log_message(f'page was modified, new Etag is {response.headers["Etag"]}')
                    async with lock:
                        current_etag = response.headers['Etag']
                    await check_if_new_news_appears(await response.text(), start_session_time, finish_session_time)


if __name__ == '__main__':
    asyncio.run(get_rss_data())