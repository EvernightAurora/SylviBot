import asyncio
import time


class DownloadingLock:
    def __init__(self, over_wait = 30):
        self.over_wait = over_wait
        self.download_dict = {}

    async def downloading_lock(self, key):
        if key in self.download_dict.keys():
            while self.download_dict[key] + self.over_wait > time.time():
                await asyncio.sleep(.2)
        self.download_dict[key] = time.time()
        return self.download_dict[key]

    def unlock(self, key, tick):
        assert key in self.download_dict
        if self.download_dict[key] == tick:
            self.download_dict[key] = 0

    async def locking(self, key):

        class _little_lock:
            def __init__(self, lock, key, tick):
                self.lock = lock
                self.key = key
                self.tick = tick

            def __enter__(self):
                pass

            def __exit__(self, exc_type, exc_val, exc_tb):
                self.lock: DownloadingLock
                self.lock.unlock(self.key, self.tick)
        return _little_lock(self, key, await self.downloading_lock(key))
