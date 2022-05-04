from mirai.models.events import FriendMessage, GroupMessage
from mirai import Mirai
from utils import JsonStore
from utils import ParseOrder
import asyncio
import time
from Proc import HelpProc
import sys


Subscribes: JsonStore.JsonStore
Inited = False
this_bot: Mirai


helper_doc_0 = '''
<所有订阅
用法: <所有订阅
按照顺序打印本群所有的打印，并且会在[]中标上临时编号
你可以通过编号来指定给<取消订阅 功能来取消某个订阅
'''

helper_doc_1 = '''
<取消订阅
用法: <取消订阅 <ind>
取消指定编号的订阅，不可撤销qwq
编号可通过<所有订阅 打印的[]中的数字获得。这个编号不固定，会随时变动
所以请在<取消订阅 前先<所有订阅
'''


def on_init():
    global Inited, Subscribes
    if Inited:
        return
    Inited = True
    Subscribes = JsonStore.JsonStore('data/subscribe/AllSubscribe.json')
    HelpProc.register_helper(['<所有订阅'], helper_doc_0)
    HelpProc.register_helper(['<取消订阅'], helper_doc_1)


def get_event_fid(event):
    if type(event) is GroupMessage:
        event: GroupMessage
        return 'G' + str(event.group.id)
    elif type(event) is FriendMessage:
        event: FriendMessage
        return 'F' + str(event.sender.id)
    else:
        raise ValueError('unknown event type ' + repr(event))


async def get_sender(bot: Mirai, fid):
    typ = fid[0]
    fid = fid[1:]
    if typ == 'G':
        return await bot.get_group(int(fid))
    elif typ == 'F':
        return await bot.get_friend(int(fid))
    else:
        raise ValueError('unknown fid ' + typ + fid)


def unpack_fid(fid):
    typ = fid[0]
    fid = fid[1:]
    fid = int(fid)
    if typ == 'G':
        return 'Group', fid
    elif typ == 'F':
        return 'Friend', fid
    else:
        raise ValueError('unknown fid ' + typ + str(fid))


async def track_fid(bot: Mirai, fid):
    w, fid = unpack_fid(fid)
    if w == 'Group':
        return await bot.get_group(fid)
    elif w == 'Friend':
        return await bot.get_friend(fid)


#   subscribe info:
#   one subscribe:
#   {   target: fid,
#       time: when it subscribe,
#       description: how to say to user,
#       type_name: name that registered,
#       args: arg that send to name}
#
#
#   register info:
#   [   type_name: name of this type,
#       async sign_func(bot, fid, args): func to sign this,
#       async quit_func(bot, fid, args): func to quit this,
#       description: may be useful description]


Registered = dict()


async def runtime_login(target, description, type_name, args):
    one = {'target': target,
           'time': time.time(),
           'description': description,
           'type_name': type_name,
           'args': args}
    if target not in Subscribes.get_data().keys():
        Subscribes.get_data()[target] = []
    await call_login_func(one)
    Subscribes.get_data()[target].append(one)
    Subscribes.flush()


def register_type(type_name: str, sign_func, quit_func, description):
    if type_name in Registered.keys():
        raise KeyError(type_name + ' already registered')
    Registered[type_name] = {"type_name": type_name,
                             "sign_func": sign_func,
                             "quit_func": quit_func,
                             "description": description}


def remove_type(type_name: str):
    if type_name not in Registered.keys():
        raise KeyError(type_name + ' not registered')
    Registered.pop(type_name)


def get_registered_sign_func(type_name: str):
    return Registered[type_name]["sign_func"]


def get_registered_quit_func(type_name: str):
    return Registered[type_name]["quit_func"]


async def call_login_func(one):
    global this_bot
    type_name = one['type_name']
    target = one['target']
    args = one['args']
    func = get_registered_sign_func(type_name)
    ret = func(this_bot, target, args)
    if asyncio.iscoroutinefunction(func):
        await ret


async def call_quit_func(one):
    global this_bot
    type_name = one['type_name']
    target = one['target']
    args = one['args']
    func = get_registered_quit_func(type_name)
    ret = func(this_bot, target, args)
    if asyncio.iscoroutinefunction(func):
        await ret


async def on_startup(bot: Mirai):
    global this_bot
    this_bot = bot
    if 'no_subscribe' in sys.argv or 'nosubscribe' in sys.argv:
        print('skiping subscribe core')
        return
    print('subscribe core startup')
    if 'log_subscribe' in sys.argv or 'logsubscribe' in sys.argv:
        print('subscribe info into subscribe.log')
        out0 = sys.stdout
        sys.stdout = open('subscribe.log', 'w')
    cnt = 0
    for qid in Subscribes.get_data().keys():
        for one in Subscribes.get_data()[qid]:
            if 'no_morning' in sys.argv and one['type_name'] == 'Greeting_Subscriber':
                print('greeting subscribe skipped')
            else:
                await call_login_func(one)
                cnt += 1
    if 'log_subscribe' in sys.argv:
        sys.stdout.close()
        sys.stdout = out0
    print('subscribe core startup end, in sum %d subscribes' % cnt)


last = {}


def reply_login(qid):
    chain = []
    global last
    last[qid] = []
    if qid not in Subscribes.get_data().keys():
        return ['没有订阅~']
    for one in Subscribes.get_data()[qid]:
        time0 = one['time']
        time_c = time.strftime("%Y-%m-%d", time.localtime(time0))
        description = one['description']
        chain.append("[%d]创建时间: %s\n描述:%s\n" % (len(last[qid]), time_c, description))
        last[qid].append(one)
    if not chain:
        chain = ['没有订阅~']
    return chain


async def proc_logout(bot: Mirai, event, fid, ind, sok=True):
    if fid not in last:
        await bot.send(event, '请先查看所有订阅再取消')
        return
    if ind < 0 or ind >= len(last[fid]):
        await bot.send(event, "ind不合法")
        return
    if last[fid][ind] is None:
        await bot.send(event, '该订阅之前已被删除')
        return
    one = last[fid][ind]
    last[fid][ind] = None
    await call_quit_func(one)
    new_list = []
    for two in Subscribes.get_data()[fid]:
        if two != one:
            new_list.append(two)
    Subscribes.get_data()[fid] = new_list
    Subscribes.flush()
    if sok:
        await bot.send(event, '取消订阅成功~')


doc = [
    ["root: <subscribecore.showall", "显示所有群的订阅"],
    ['<subscribecore.showthis', "显示这个群的订阅"],
    ['<subscribecore.logout <ind>', "取消上面显示的"],
    ['root: <subscribecore.logout_from <source>', '取消一个fid的所有人的订阅'],
    ['root: <subscribecore.logout_from <source> <id>', '取消一个人的某个订阅']
]


def root_proc(bot: Mirai, event, msg: str):
    result, _ = ParseOrder.detect_order(msg, '<subscribecore.showall')
    if result:
        chain0 = ['--------\n']
        for qid in Subscribes.get_data().keys():
            if chain0:
                chain0.append('\n\n')
            chain0.append('[**** %s ****]\n' % qid)
            chain = reply_login(qid)
            chain0.extend(chain)
        return bot.send(event, chain0)

    result, nlast = ParseOrder.detect_order(msg, '<subscribecore.logout_from', [0, 1, 2])
    if result:
        if len(nlast) == 0:
            fid = get_event_fid(event)
        else:
            fid = nlast[0]
        try:
            _ = unpack_fid(fid)
        except ValueError:
            return bot.send(event, 'fid错误')
        reply_login(fid)

        async def d_all():
            cnt = 0
            global last
            if len(nlast) < 2:
                for lasti in range(len(last[fid])):
                    await proc_logout(bot, event, fid, lasti, sok=False)
                    cnt += 1
            else:
                ind = int(nlast[1])
                await proc_logout(bot, event, fid, ind, sok=False)
                cnt += 1
            await bot.send(event, '取消订阅成功*' + str(cnt))
        return d_all()

    return None


def proc(bot: Mirai, event, msg: str):
    result, _ = ParseOrder.detect_order(msg, '<subscribecore.showthis')
    if result:
        fid = get_event_fid(event)
        chain = reply_login(fid)
        return bot.send(event, chain)

    result, last = ParseOrder.detect_order(msg, '<subscribecore.logout', 1)
    if result:
        last = last[0].strip()
        try:
            last = int(last)
        except ValueError:
            return bot.send(event, 'ind只能是数字')
        return proc_logout(bot, event, get_event_fid(event), last)
    return None
