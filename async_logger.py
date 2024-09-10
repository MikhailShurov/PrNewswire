import logging
import asyncio
# import aiofiles
# ToDo rewrite with aiofiles

class AsyncLogger:
    def __init__(self, name='AsyncLogger', level=logging.DEBUG):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        handler = logging.FileHandler('async_app.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        self.queue = asyncio.Queue()
        # ToDo rewrite it with aiofiles

    async def run(self):
        while True:
            try:
                message = self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            level, log = message
            self.logger.log(level, log)

    async def log(self, level, message):
        await self.queue.put((level, message))
        task = asyncio.create_task(self.run())
        await task

    async def shutdown(self):
        await self.queue.put(None)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown()


async def get_async_logger():
    return AsyncLogger()
