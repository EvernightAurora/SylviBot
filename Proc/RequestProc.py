from mirai import Mirai
from mirai.models.events import RequestEvent, MemberJoinRequestEvent, NewFriendRequestEvent
from mirai.models.events import BotInvitedJoinGroupRequestEvent
from mirai.models.entities import Subject
from utils import ImgDataStore
from utils import ParseOrder, configLoader


Requests: ImgDataStore.ImageData


def on_init():
    global Requests
    Requests = ImgDataStore.ImageData('Requests.json')


doc = [
    ['root: <request.showall', '显示当前所有委托'],
    ['root: <request.decline <index>', '拒绝编号i的委托'],
    ['root: <request.accept <index>', '允许编号i的委托']
]
last = []


def p_repr(event):
    if type(event) is NewFriendRequestEvent:
        return repr(event)[:-1] + ', groupId=0)'
    else:
        return repr(event)[:-1] + ", message='')"


async def on_requests(bot: Mirai, event: RequestEvent):
    key = str(str(event.from_id) + '-' + str(event.from_id))
    for qq in configLoader.get_config('root_qq', []):
        await bot.send(await bot.get_friend(qq), str(event))
    Requests.add(key, p_repr(event))


async def on_showall(bot: Mirai, event):
    chain = []
    global last
    last = []
    data = Requests.get_data()
    for k in data.keys():
        chain.append('[%d]' % len(last) + repr(data[k]))
        chain.append('\n')
        last.append(k)
    if not chain:
        chain.append('咩~')
    await bot.send(event, chain)
    return


async def on_process(bot: Mirai, event, ind, motivate):
    global last
    if motivate not in ['accept', 'decline']:
        await bot.send(event, "不认识的motivate " + str(motivate))
        return
    data = Requests.get_data()
    try:
        ind = int(ind)
        if ind < 0 or ind >= len(last):
            raise ValueError
    except ValueError:
        await bot.send(event, "ind不合法")
        return
    key = last[ind]
    if key not in data.keys():
        await bot.send(event, '已被处理')
    req = eval(data[key])
    if motivate == 'accept':
        await bot.allow(req)
    else:
        await bot.decline(req)
    await bot.send(event, "操作成功")
    Requests.remove(key)


def proc(bot, event, msg):
    return None


def root_proc(bot: Mirai, event, msg: str):
    result, _ = ParseOrder.detect_order(msg, '<request.showall')
    if result:
        return on_showall(bot, event)

    result, last = ParseOrder.detect_order(msg, '<request.decline', 1)
    if result:
        return on_process(bot, event, last[0], 'decline')

    result, last = ParseOrder.detect_order(msg, '<request.accept', 1)
    if result:
        return on_process(bot, event, last[0], 'accept')
    return None


if __name__ == '__main__':
    a = eval('''NewFriendRequestEvent(event_id=1644995606000000, from_id=1359585930, nick='\u03c9\u0394\u03c6', message='\u6211\u662f\u03c9\u0394\u03c6',groupId=0)''')
    pass