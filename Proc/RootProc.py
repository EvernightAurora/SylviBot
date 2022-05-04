import random
import time
import os
import sys
from mirai import Mirai


doc = [
    ['root: <eval', '执行代码'],
    ['root: <exec', '执行代码'],
    ['root: <shutdown', '杀死小仙布']
]


def root_proc(bot: Mirai, event, msg):
    msg = msg.lower()
    if msg.find('<eval ') == 0:
        last = msg[len('<eval '):]
        result = '没正常运行'
        try:
            result = eval(last)
        except:
            result = '出错啦'
        return bot.send(event, repr(result))
    if msg.find('<exec ') == 0:
        last = msg[len('<exec '):]
        try:
            exec(last)
        except:
            return bot.send(event, '<exec出错啦')
        finally:
            return bot.send(event, '<exec完成')
    if msg == '<shutdown':

        async def local_sync():
            await bot.send(event, '挥挥qaq')
            await bot.shutdown()
        return local_sync()
    return None


def proc(bot, event, msg):
    return None
