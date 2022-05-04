from mirai import Mirai, FriendMessage, WebSocketAdapter
from mirai.models.events import GroupMessage, NudgeEvent
from mirai.models.message import MessageChain
import mirai.models.message
from mirai.models.entities import Subject
import random
import time
from utils import configLoader


NUDGE_TIME_WINDOW = 10
NUDGE_TIMES_WINDOW = 10


Nudge_Save = dict()


async def attempt_nudge(bot: Mirai, fid, id, kind):
    global Nudge_Save
    fid = str(fid)
    if fid not in Nudge_Save:
        Nudge_Save[fid] = []
    if len(Nudge_Save[fid]) >= NUDGE_TIMES_WINDOW:
        if Nudge_Save[fid][0] + NUDGE_TIME_WINDOW > time.time():
            return
        Nudge_Save[fid] = Nudge_Save[fid][1:]
    Nudge_Save[fid].append(time.time())
    await bot.send_nudge(fid, id, kind)


async def on_nudge(bot: Mirai, event: NudgeEvent):
    To = event.target
    Pos = event.subject
    if event.from_id == bot.qq:
        return

    if To == bot.qq:
        if Pos.kind == 'Group':
            npos = Pos
        elif Pos.kind == 'Friend':
            npos = Subject(event.from_id, 'Friend')
        else:
            return
        await attempt_nudge(bot, event.from_id, npos.id, npos.kind)
        await attempt_nudge(bot, event.from_id, npos.id, npos.kind)
    elif To != bot.qq:
        if Pos.kind == 'Group':
            npos = Pos
        elif Pos.kind == 'Friend':
            npos = Subject(event.from_id, 'Friend')
        else:
            return
        if To in configLoader.get_config('root_qq', []):
            if random.randint(1, 3) <= 2:
                return
            await attempt_nudge(bot, event.from_id, npos.id, npos.kind)
        else:
            if random.randint(1, 5) <= 4:
                return
            await attempt_nudge(bot, To, npos.id, npos.kind)


doc = [
    ['root:<rua qid id times', '在某个群rua某位很多次']
]


def is_order(msg, str):
    return msg[:len(str)] == str


def cut_order(msg, str):
    return msg[len(str):]


def root_proc(bot, event, msg):
    msg0 = '<rua '
    if is_order(msg, msg0):
        last = cut_order(msg, msg0)
        try:
            last = last.strip().split()
            if len(last) == 2:
                last.append('1')
            if len(last) != 3:
                raise ValueError
            last[0] = int(last[0])
            last[1] = int(last[1])
            last[2] = int(last[2])
            if last[2] > 10:
                raise ValueError
        except ValueError:
            return bot.send(event, "不可以")

        async def nudge():
            qid = last[0]
            id = last[1]
            times = last[2]
            for i in range(times):
                await bot.send_nudge(id, qid, 'Group')
        return nudge()


def proc(bot, event, msg):
    return None
