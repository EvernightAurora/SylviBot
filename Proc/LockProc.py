import app
from utils import JsonStore, ParseOrder, SubscribeCore

Locked_Set = set()
Locked_Data: JsonStore.JsonStore


def on_init():
    global Locked_Data, Locked_Set
    Locked_Data = JsonStore.JsonStore('data/Lock.json')
    for i in Locked_Data.get_data().keys():
        Locked_Set.add(i)


doc = [
    ['root: <lock (<fid>)', '锁上'],
    ['root: <unlock (<fid>)', '解锁'],
    ['root: <locked (<fid>)', '有没有锁'],
    ['root: <lock.list', '哪些在锁']
]


def root_proc(bot, event, msg):
    msg = msg.lower()
    global Locked_Set, Locked_Data
    result, last = ParseOrder.detect_order(msg, '<lock', [0, 1])
    if result:
        if len(last) == 0:
            fid = SubscribeCore.get_event_fid(event)
        else:
            fid = last[0].upper()
        Locked_Data.get_data()[fid] = 0
        Locked_Set.add(fid)
        Locked_Data.flush()
        return bot.send(event, "uwu")

    result, last = ParseOrder.detect_order(msg, '<unlock', [0, 1])
    if result:
        if len(last) == 0:
            fid = SubscribeCore.get_event_fid(event)
        else:
            fid = last[0].upper()
        if fid not in Locked_Set:
            return bot.send(event, 'uwu?')
        Locked_Set.remove(fid)
        Locked_Data.get_data().pop(fid)
        Locked_Data.flush()
        return bot.send(event, 'owo')

    result, last = ParseOrder.detect_order(msg, '<locked')
    if result:
        if not last:
            fid = SubscribeCore.get_event_fid(event)
        else:
            fid = last[0].upper()
        if fid in Locked_Set:
            return bot.send(event, 'qwq')
        else:
            return bot.send(event, 'owo')
    if msg == '<lock.list':
        return bot.send(event, str(Locked_Set))


def proc(bot, event, msg):
    global Locked_Set

    if app.is_group_event(event):
        fid = SubscribeCore.get_event_fid(event)
        if fid in Locked_Set:
            return 1
    return None
