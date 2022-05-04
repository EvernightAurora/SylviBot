import httpx
import time
import asyncio


class AsyncClientControl:
    def __init__(self, cnt, wait_time=4., headers=None, cookies=None, httpx_timeout=None, proxies=None):
        self.CLIENT_WAIT_TIME = wait_time
        self.CLIENT_NUM = cnt
        self.Clients = []
        self.CLIENT_LAST_USE = [0]*cnt
        for i in range(self.CLIENT_NUM):
            Client = httpx.AsyncClient(timeout=httpx_timeout, proxies=proxies)
            if cookies:
                for i in cookies.keys():
                    Client.cookies[i] = cookies[i]
            if headers:
                Client.headers = headers
            self.Clients.append(Client)

    async def alloc_client(self):
        earliest = 0
        while True:
            earliest = 0
            for i in range(self.CLIENT_NUM):
                if self.CLIENT_LAST_USE[i] < self.CLIENT_LAST_USE[earliest]:
                    earliest = i
            if self.CLIENT_LAST_USE[i] + self.CLIENT_WAIT_TIME < time.time():
                break
            await asyncio.sleep(0.2)
        self.CLIENT_LAST_USE[earliest] = time.time()
        return self.Clients[earliest], self.CLIENT_LAST_USE[earliest]

    def free_client(self, clt, tim):
        for i in range(self.CLIENT_NUM):
            if self.Clients[i] == clt:
                if self.CLIENT_LAST_USE[i] == tim:
                    self.CLIENT_LAST_USE[i] = 0
                return
        print('cant find client?')
