from utils.fixed_size_cache import FixedSizeCache


class GlobalCache(FixedSizeCache):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(GlobalCache, cls).__new__(cls)
        return cls._instance

    def __init__(self, size=10):
        # Инициализация только если это первый вызов
        if not hasattr(self, 'initialized'):
            super().__init__(size)
            self.initialized = True
