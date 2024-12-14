import requests_cache
from contextlib import contextmanager
import requests_cache


class CacheManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        """Inicializa o cache"""
        self.session = requests_cache.CachedSession(
            'statsbomb_cache',
            backend='sqlite',
            expire_after=3600
        )

    @contextmanager
    def get_session(self):
        """Get a cached session"""
        try:
            yield self.session
        finally:
            pass


cache_manager = CacheManager()
