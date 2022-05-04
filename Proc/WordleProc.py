from mirai import Mirai, FriendMessage, GroupMessage
from mirai.models.message import Image, Quote, Plain
from mirai.models.entities import GroupMember, Friend
from utils import Pokewiki
import cv2
import os
import numpy as np
import random
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import time
from utils import ParseOrder
from utils import SubscribeCore, VisStore, ImgDataStore
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt


YELLOW_COLOR = [220, 167, 7]
BLACK_COLOR = [51, 65, 85]
GREEN_COLOR = [32, 183, 88]
BLANK_COLOR = [169, 182, 199]
DEFAULT_CD = 1800       # 30min
TIME_LIMIT = 1800
Word_Store = []
Word_Vis: VisStore.SeenPicture
Wait_CD: ImgDataStore.ImageData
Last_Word: ImgDataStore.ImageData
q_Flow = 0
Store_Data = dict()     # "fid-mid" : {is_group:bool, guess_list:list, true_word:str, start_time:float, qid:}


def on_init():
    global Word_Vis, Word_Store, Wait_CD, Last_Word
    with open('data/Wordle/wordle_stock.txt') as f:
        words = f.read()
    words = words.split('\n')
    Word_Store = [s.strip().upper() for s in words if len(s.strip()) == 5]
    Word_Vis = VisStore.SeenPicture('data/Wordle/WordleSeen.json')
    Wait_CD = ImgDataStore.ImageData('data/Wordle/Wait_CD.json')
    Last_Word = ImgDataStore.ImageData('data/Wordle/Last_Word.json')


def random_word(fid):
    global Word_Vis, Word_Store
    pack = [(Word_Vis.seen_count(fid, i), i) for i in Word_Store]
    random.shuffle(pack)
    pack = sorted(pack, key=lambda i: i[0])
    Word_Vis.saw_again(fid, pack[0][1])
    return pack[0][1]


def proper_mid(id):
    if id < 0:
        return id + 65546
    else:
        return id


def decide_color(guess, word, pos):
    if guess[pos] == word[pos]:
        return GREEN_COLOR
    for i in range(len(word)):
        if guess[i] == word[i]:
            guess = guess[:i] + '-' + guess[i+1:]
            word = word[:i] + '-' + word[i+1:]
    color = []
    for i in range(len(word)):
        if guess[i] != '-':
            if guess[i] in word:
                color.append(YELLOW_COLOR)
                pos0 = word.find(guess[i])
                word = word[:pos0] + '-' + word[pos0+1:]
            else:
                color.append(BLACK_COLOR)
        else:
            color.append(0)
    return color[pos]


def paint_wordle(guess_s, true_world):
    plt.figure(figsize=(5, 6), facecolor=np.array([222, 222, 222])/255.)
    plt.clf()
    plt.subplots_adjust(left=.03, bottom=.03, right=.97, top=.97, wspace=.16, hspace=.16)
    for w in range(6):
        for h in range(5):
            plt.subplot(6, 5, w*5+h+1)
            plt.axis('off')
            if w >= len(guess_s):
                plt.imshow([[BLANK_COLOR]])
            else:
                plt.imshow([[decide_color(guess_s[w], true_world, h)]])
                plt.text(0, 0.1, guess_s[w][h], horizontalalignment='center', verticalalignment='center',
                         fontsize=45, color='w', weight='black')


def is_in_cd(fid):  # none if not, else return str of len
    if fid[0] not in ['g', 'G']:
        return None
    global Last_Word, Wait_CD, DEFAULT_CD
    if Last_Word.has(fid):
        last = Last_Word.get(fid)
    else:
        return None
    if Wait_CD.has(fid):
        cd = Wait_CD.get(fid)
    else:
        cd = DEFAULT_CD
    if last + cd <= time.time():
        return None
    last = last + cd - time.time()
    if last < 60:
        return '%.1fs' % last
    last /= 60
    if last < 60:
        return '%.1fm' % last
    last /= 60
    return '%.1fh' % last


def refresh_cd(fid, zero=False):
    global Last_Word
    if zero:
        Last_Word.add(fid, 0)
    else:
        Last_Word.add(fid, time.time())


g_flow = 0


def generate_img(guess, true):
    global g_flow
    file_name = '%02d.png' % g_flow
    g_flow += 1
    g_flow %= 100
    paint_wordle(guess[-6:], true)
    dir0 = 'data/buffer/Wordle/'
    os.makedirs(dir0) if not os.path.exists(dir0) else None
    to_file = os.path.join(dir0, file_name)
    plt.savefig(to_file, dpi=60)
    return to_file


async def try_start_game(bot: Mirai, event):
    global q_Flow, Store_Data
    fid = SubscribeCore.get_event_fid(event)
    result = is_in_cd(fid)
    if result:
        await bot.send(event, '下一次还要等待%s哟~' % result)
        return
    refresh_cd(fid)
    word = random_word(fid)
    guess = []
    ntime = time.time()
    q_Flow += 1
    args = {
        'is_group': type(event) is GroupMessage,
        'guess_list': guess,
        'start_time': ntime,
        'true_word': word,
        'qid': q_Flow
    }
    fn = generate_img(guess, word)
    mid = await bot.send(event,
                         ['这次的Wordle~,  #%d' % q_Flow, Image(path=fn),
                          '回复最新的消息来回答，无限次机会~(私聊为6次)\n来自4级词汇，5字母，绿:正确，黄:有这个字母但位置不对，黑：没这个字母'])
    d_id = fid + '-' + str(proper_mid(mid))
    Store_Data[d_id] = args
    print('#%d' % q_Flow + ' 猜的词 其实是 ' + word)


def is_reply(bot, event):
    quote = None
    event: GroupMessage
    for i in event.message_chain:
        if type(i) is Quote:
            quote = i
            break
    if not quote:
        return False
    fid = SubscribeCore.get_event_fid(event)
    mid = proper_mid(quote.id)
    cora = fid + '-' + str(mid)
    global Store_Data
    if cora in Store_Data.keys():
        return cora
    return False


async def on_reply(bot: Mirai, event):
    full = is_reply(bot, event)
    assert not not full
    global Store_Data, TIME_LIMIT, Word_Store
    args = Store_Data[full]
    if args['start_time'] + TIME_LIMIT <= time.time():
        Store_Data.pop(full)
        await bot.send(event, '这个过去太久啦~', quote=True)
        return
    word = ''
    for i in event.message_chain:
        if type(i) is Plain:
            word += str(i).strip()
    word = word.upper()
    if len(word) != 5:
        await bot.send(event, '是5个字母嘛', quote=True)
        return
    if word not in Word_Store:
        await bot.send(event, word + ' 不在词汇表里，是不是太高级的词汇呀uwu', quote=True)
        return
    args['guess_list'].append(word)
    Store_Data.pop(full)
    g_img = generate_img(args['guess_list'], args['true_word'])
    if word == args['true_word']:
        await bot.send(event, ['恭喜答对啦ww #%d' % args['qid'], Image(path=g_img)], quote=True)
        return
    if not args['is_group'] and len(args['guess_list']) == 6:
        await bot.send(event, ['到达限制啦qwq #%d' % args['qid'], Image(path=g_img), '正确答案是%s' % args['true_word']],
                       quote=True)
        return
    nid = await bot.send(event, ['%dth ,#%d' % (len(args['guess_list']), args['qid']),
                                 Image(path=g_img), '\n绿:正确，黄:字正确位置不对，黑:没这个字'])
    fid = SubscribeCore.get_event_fid(event)
    make_id = fid + '-' + str(proper_mid(nid))
    Store_Data[make_id] = args
    return

doc = [
    ['root:<wordle.refresh <id>', '清空本群(或指定群)的cd'],
    ['root:<wordle.setcd <sec>', '设置本群的wordle cd(单位:s)'],
    ['<wordle.start', '尝试开始一局wordle']
]


def root_proc(bot: Mirai, event, msg):
    result, fid = ParseOrder.detect_order(msg, '<wordle.refresh', [0, 1])
    if result:
        if fid:
            fid = fid[0]
        else:
            fid = SubscribeCore.get_event_fid(event)
        global Last_Word
        if not Last_Word.has(fid):
            return bot.send(event, '不需要嘛，是不是没这个群')
        refresh_cd(fid, zero=True)
        return bot.send(event, '成功~')

    result, sec = ParseOrder.detect_order(msg, '<wordle.setcd', 1)
    if result:
        sec = sec[0]
        try:
            sec = int(sec)
        except ValueError:
            return bot.send(event, str(sec) + ' 不是整数嘛')
        global Wait_CD
        Wait_CD.add(SubscribeCore.get_event_fid(event), sec)
        return bot.send(event, '成功修改cd为%ds' % sec)


def proc(bot: Mirai, event, msg):
    result, _ = ParseOrder.detect_order(msg, '<wordle.start')
    if result:
        return try_start_game(bot, event)

    if is_reply(bot, event):
        return on_reply(bot, event)
