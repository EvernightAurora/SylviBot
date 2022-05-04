from mirai import Mirai, FriendMessage
from mirai.models.events import GroupMessage
from mirai.models.message import MessageChain
import random
import urllib
import mirai.models.message
from Proc import NudgeProc
from utils import Pokewiki
from Proc import HelpProc

doc = [
    ['<wiki.search name', '尝试查找宝可梦']
]

helper_doc_0 = '''
<查询
用法 <查询 <名字、全国编号>
试图查询宝可梦的信息，并返回一小段简介
例子:
    <查询 草伊布
'''


def on_init():
    Pokewiki.on_init()
    HelpProc.register_helper(['<查询'], helper_doc_0)


def root_proc(bot, event, msg):
    return None


def proc(bot: Mirai, event: FriendMessage, msg):
    if NudgeProc.is_order(msg, '<wiki.search '):
        last = NudgeProc.cut_order(msg, '<wiki.search ')
        last = last.strip()
        is_match, result = Pokewiki.find_pokemon(last)
        if type(event) is GroupMessage:
            chain = [mirai.At(event.sender.id), "\n"]
        else:
            chain = []
        if not result:
            chain.append("查不到uwu")
            return bot.send(event, MessageChain(chain))
        if not is_match:
            chain.append("也许您找的是这个\n")
            result = random.choice(result)
        id0 = Pokewiki.Pokemon_List[result][0]
        chain.append("全国图鉴编号: " + id0 + '\n')
        name = Pokewiki.Pokemon_List[result][1]
        chain.append(mirai.Image(path="wiki/imgs/" + id0 + '.png'))
        chain.append("\n" + Pokewiki.Pokemon_Intro[id0].strip())
        chain.append(("\n" + 'https://wiki.52poke.com/wiki/' + urllib.parse.quote(name)))
        return bot.send(event, MessageChain(chain))
    return None
