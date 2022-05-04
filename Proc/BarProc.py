from tqdm import tqdm
import time
from mirai import Mirai
import io


TIME_LIMIT = 11


class Single_Bar:
    def __init__(self, total, id, name):
        self.id = id
        self.name = name
        self.lasttime = time.time()
        self.ioflow = io.StringIO()
        self.bar = tqdm(total=total, file=self.ioflow, unit_scale=True, unit_divisor=1024, unit="B")

    def update(self, n):
        self.bar.update(n)
        self.lasttime = time.time()


BarPool = dict()
BarId = 0


def register_bar(total, name):
    auto_remove()
    global BarPool, BarId
    BarId += 1
    BarPool[BarId] = Single_Bar(total=total, id=BarId, name=name)
    return BarId


def auto_remove():
    global BarPool
    removes = []
    for id in BarPool.keys():
        if BarPool[id].lasttime + TIME_LIMIT < time.time():
            removes.append(id)
    for id in removes:
        BarPool.pop(id)


def update_bar(id, n):
    auto_remove()
    global BarPool
    if id not in BarPool.keys():
        raise KeyError("not have the id in bar")
    BarPool[id].update(n)


def release_bar(id):
    auto_remove()
    global BarPool
    if id not in BarPool.keys():
        raise KeyError("not have the id in bar when release")
    BarPool.pop(id)


doc = [
    ['<bar.query', '查询当前的进度条信息']
]


def root_proc(bot, event, msg):
    return None


def proc(bot: Mirai, event, msg: str):
    if msg.lower() == '<bar.query':
        message = ""
        auto_remove()
        for id in BarPool.keys():
            bar = BarPool[id]
            message += '***' + bar.name + '\n'
            message += bar.ioflow.getvalue().split('\r')[-1] + '\n'
        if message == "":
            message = "空~"
        return bot.send(event, message)
    return None
