import asyncio
import time


class SendLock:
    def __init__(self, overtime=10, per_wait=0.2):
        self.overtime = overtime
        self.last_time = 0
        self.per_wait = per_wait

    async def wait_lock(self):
        while time.time() - self.last_time < self.overtime:
            await asyncio.sleep(self.per_wait)
        self.last_time = time.time()
        return self.last_time

    def unlock(self, last_time):
        if last_time == self.last_time:
            self.last_time = 0

    async def locking(self):

        class with_class:
            def __init__(self, lock, key):
                self.lock = lock
                self.key = key

            def __enter__(self):
                pass

            def __exit__(self, exc_type, exc_val, exc_tb):
                self.lock: SendLock
                self.lock.unlock(self.key)

        key = await self.wait_lock()
        return with_class(self, key)


global_wait = SendLock()
