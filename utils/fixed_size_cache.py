import asyncio


class FixedSizeCache:
    def __init__(self, size=10):
        self.size = size
        self.cache = []
        self._lock = asyncio.Lock()

    async def add(self, item):
        async with self._lock:
            if len(self.cache) >= self.size:
                self.cache.pop(0)
            self.cache.append(item)

    async def top(self):
        async with self._lock:
            if self.cache:
                return self.cache[-1]
            return None

    async def contains(self, item):
        async with self._lock:
            return item in self.cache

    def __repr__(self):
        result = ''.join(str(self.cache[i]) + '\n' for i in range(len(self.cache) - 1, -1, -1))
        return result
