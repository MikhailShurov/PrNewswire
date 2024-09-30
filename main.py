import asyncio
from scrapers import json_scraper, rss_scraper, html_scraper


async def start():
    await asyncio.gather(
        json_scraper.get_data(),
        rss_scraper.get_data(),
        html_scraper.get_data(),
    )


if __name__ == '__main__':
    asyncio.run(start())
