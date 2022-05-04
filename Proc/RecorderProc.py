from mirai import Mirai, FriendMessage, GroupMessage
import mirai.models.message
from mirai.models.message import *
from mirai.models.message import Image, HttpUrl, FlashImage, At, AtAll, App, MessageChain, Plain, Dice, Face, File
from mirai.models.message import Forward, Json, MusicShare, Poke, PokeNames, Quote, Source, Voice, Xml
from mirai.models.message import ForwardMessageNode
from mirai.models.entities import GroupMember, Friend, Group
import datetime

import json
import os
import signal
import time
from Proc import NudgeProc


SEND_LIMIT = 50
doc = [
    ["root: <record.showall", "显示所有储存的record"],
    ["root: <record.group.get id", "得到指定的群聊天记录"],
    ["root: <record.friend.get id", "得到指定的好友聊天记录"],
    ["root: <record.get id", "按照特定list显示的id得到"]
]


def get_tape_filepath(typ: str, id):
    if typ == 'Friend':
        return os.path.join("Record", typ, str(id) + '.txt')
    if typ == 'Group':
        return os.path.join("Record", typ, str(id) + '.txt')
    raise Exception("not have this type")


def get_tape(path):
    if os.path.isfile(path):
        with open(path, 'r') as f:
            ret = json.load(f)
    else:
        ret = ['None']
    return ret


def waiting_handler(signal, frame):
    print('saving please wait')


def save_tape(path, tape):
    prev = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, waiting_handler)
    if not os.path.exists(os.path.split(path)[0]):
        os.makedirs(os.path.split(path)[0])
    with open(path, 'w') as f:
        json.dump(tape, f, indent=2)
    signal.signal(signal.SIGINT, prev)


def get_fresh_time():
    if os.path.isfile("Record/Fresh.json"):
        with open("Record/Fresh.json", 'r') as f:
            ret = json.load(f)
        return ret
    return dict()


def flush_fresh_time(dt):
    prev = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, waiting_handler)
    with open("Record/Fresh.json", 'w') as f:
        json.dump(dt, f, indent=2)
    signal.signal(signal.SIGINT, prev)


def proc(bot, event, msg):
    return None


def record_proc(bot: Mirai, event, msg):
    fresh = get_fresh_time()
    if type(event) is FriendMessage:
        id = event.sender.id
        if id == bot.qq:
            return None
        fresh[str(id)] = time.time()
        Previous = get_tape(get_tape_filepath("Friend", id))
        Previous.append(repr(event))
        save_tape(get_tape_filepath("Friend", id), Previous)
    elif type(event) is GroupMessage:
        id = event.group.id
        fresh[str(id)] = time.time()
        Previous = get_tape(get_tape_filepath("Group", id))
        Previous.append(repr(event))
        save_tape(get_tape_filepath("Group", id), Previous)
    flush_fresh_time(fresh)
    return None


list_buff = []


def proper_time_interval(secs):
    if secs < 120:
        return "%.2f s" % secs
    secs /= 60
    if secs < 120:
        return "%.2f m" % secs
    secs /= 60
    if secs < 48:
        return "%.2f h" % secs
    secs /= 24
    return "%.2f d" % secs


async def show_list(bot: Mirai, event: FriendMessage):
    global list_buff
    list_buff = []
    message_chain = ""
    message_chain += "**Friend:\n"
    fresh = get_fresh_time()
    chains = []
    for f in os.listdir("Record/Friend"):
        if f[-3:] == 'txt':
            nid = f[:-4]
            he = await bot.get_friend(int(nid))
            chains.append((-fresh[str(nid)], he, nid))
    chains = sorted(chains, key=lambda x: x[0])
    for _, he, id0 in chains:
        if not he:
            nick = '<已被删>'
        else:
            nick = he.nickname
        message_chain += '[%d]' % len(list_buff) + nick + '(' + str(id0) + ')\n'
        message_chain += '\t\t %s ago\n' % (proper_time_interval(time.time() - fresh[str(id0)]))
        list_buff.append(['Friend', id0])
    message_chain += '\n\n**Group:\n'
    chains = []
    for f in os.listdir("Record/Group"):
        if f[-3:] == 'txt':
            nid = f[:-4]
            gp = await bot.get_group(int(nid))
            if not gp:
                gp = Group(id=int(nid), name=str("<已不在这个群>"), permission='MEMBER')
            chains.append((-fresh[str(gp.id)], gp))
    chains = sorted(chains, key=lambda x:x[0])
    for _, gp in chains:
        message_chain += '[%d]' % len(list_buff) + gp.name + '(' + str(gp.id) + ')\n'
        message_chain += '\t\t %s ago\n' % (proper_time_interval(time.time() - fresh[str(gp.id)]))
        list_buff.append(['Group', gp.id])
    await bot.send(event, message_chain)


def proper_record(tape):
    Msg = []
    for i in tape:
        if 'MusicShare' in i:
            continue
        i = eval(i)
        if type(i) is GroupMessage:
            # i = GroupMessage(i)
            tim = (i.message_chain[0]).time
            name = i.sender.member_name
            id = i.sender.id
        elif type(i) is FriendMessage:
            # i = FriendMessage(i)
            tim = (i.message_chain[0]).time
            name = i.sender.nickname
            id = i.sender.id
        else:
            continue
        # tim = datetime.datetime(tim)
        tim = tim.astimezone()
        tim = str(tim)[:-6]
        Msg.append("[***]" + tim + ": " + str(name) + "[" + str(id) + ']:\n')
        for msg in i.message_chain[1:]:
            if type(msg) is Image or type(msg) is Plain or type(msg) is Face:
                Msg.append(msg)
            else:
                Msg.append(str(msg))
        Msg.append("\n")
    return Msg


def root_proc(bot, event, msg):
    global list_buff
    if msg == "<record.showall":
        return show_list(bot, event)
    if NudgeProc.is_order(msg, "<record.group.get "):
        id = NudgeProc.cut_order(msg, "<record.group.get ")
        try:
            id = int(id.strip())
        except ValueError:
            return bot.send(event, "不行")
        fp = get_tape_filepath("Group", id)
        if os.path.isfile(fp):
            data = get_tape(fp)
            if len(data) > SEND_LIMIT:
                data = data[-SEND_LIMIT:]

            return bot.send(event, proper_record(data))
        else:
            return bot.send(event, "没有")
    if NudgeProc.is_order(msg, "<record.friend.get "):
        id = NudgeProc.cut_order(msg, "<record.friend.get ")
        try:
            id = int(id.strip())
        except ValueError:
            return bot.send(event, "不行")
        fp = get_tape_filepath("Friend", id)
        if os.path.isfile(fp):
            data = get_tape(fp)
            if len(data) > SEND_LIMIT:
                data = data[-SEND_LIMIT:]
            return bot.send(event, proper_record(data))
        else:
            return bot.send(event, "没有")
    if NudgeProc.is_order(msg, "<record.get "):
        id = NudgeProc.cut_order(msg, "<record.get ")
        try:
            id = int(id.strip())
            if id<0 or id>=len(list_buff):
                raise ValueError
        except ValueError:
            return bot.send(event, "不行")
        fp = get_tape_filepath(list_buff[id][0], list_buff[id][1])
        if os.path.isfile(fp):
            data = get_tape(fp)
            if len(data) > SEND_LIMIT:
                data = data[-SEND_LIMIT:]
            return bot.send(event, proper_record(data))
        else:
            return bot.send(event, "没有")
    return None
