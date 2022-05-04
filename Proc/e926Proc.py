from mirai.models.message import MessageChain
from utils import e926
import mirai.models.message
from utils import VisStore
import app


Seen: VisStore.SeenPicture


def on_init():
    global Seen
    Seen = VisStore.SeenPicture('imgs/e926.json')
    e926.on_init()


doc = [
    ['root: <img.e926.dset <...>', '设置默认标签'],
    ['root: <img.e926.clearseen', '清除已看图片'],
    ['<img.e926.tset <int>', '设置阈值'],
    ['<img.e926.unset', '设置回默认'],
    ['<img.e926.rget', '随机寻找图片'],
    ['<img.e926.pget <ind>', '搜索给定ind的预设方案'],
    ['<img.e926.get <标签>', '在特定的标签中寻找第一个, 默认有order:random'],
    ['<img.e926.preset', '输出预设方案'],
    ['<img.e926.default', '显示当前随机搜索标签'],
    ['<img.e926.local', '显示一点点本群统计数据']
]

preset = [
    [e926.norm_search_r0, '伊布'],
    ['alolan_vulpix feral', '六尾'],
    ['pokemon score:>=300', '优质（也许）的任意宝可梦'],
    ['hioshiru score:>=0 pokemon', 'hio大大的宝可梦图'],
    ['pridark score:>=0 -my_little_pony', '另一个觉得不错的画师']
]


def filter_by_seen(event, l):
    if l == []:
        return l
    id = None
    if app.is_group_event(event):
        id = event.group.id
    else:
        id = event.sender.id
    l2 = [(Seen.seen_count(id, l[a]['id']), a) for a in range(len(l))]
    l2 = sorted(l2)
    return [l[a[1]] for a in l2]


def root_proc(bot, event, msg):
    msg = msg.lower()
    if msg == '<img.e926.clearseen':
        id = None
        if app.is_group_event(event):
            id = event.group.id
        else:
            id = event.sender.id
        Seen.clear_seen(id)
        return bot.send(event, '已清除已看过图片数据')

    if msg.find('<img.e926.dset ') == 0:
        last = msg[len('<img.e926.dset '):]
        s = last.strip()
        e926.norm_search = s
        return bot.send(event, "成功设置e621.norm_search 为 " + s)


def collect_image(bot, event, key=None):
    if key:
        l = e926.get_searchs(key)
    else:
        l = e926.get_searchs()
    l = filter_by_seen(event, l)
    if len(l) < 1:
        return bot.send(event, "找不到qaq")
    out = l[0]
    path = e926.download_image(out)

    id = None
    if app.is_group_event(event):
        id = event.group.id
    else:
        id = event.sender.id
    Seen.saw_again(id, out['id'])

    return bot.send(event, MessageChain([
        '来啦w\n',
        mirai.models.message.Image(path=path),
        'score:%d, favor: %d rating:%s  已看过:%d次 链接url:\n%s' %
        (out['score'], out['fav'], out['rating'], Seen.seen_count(id, out['id']), r'https://e926.net/posts/' + out['id'])
    ]))


def proc(bot, event, msg):
    msg = msg.lower()
    if msg == '<img.e926.rget' or msg == '<img.e926.get':
        print("上好的e图")
        return collect_image(bot, event)
    if msg.find('<img.e926.get ') == 0:
        last = msg[len('<img.e926.get '):]
        last = last.strip()
        print("中好的e图 " + last)
        return collect_image(bot, event, last)

    if msg == '<img.e926.default':
        return bot.send(event, "目前e926站的默认搜索: " + e926.norm_search_r + "\n score阈值: " + str(e926.score_threshold_r))

    if msg == '<img.e926.unset':
        e926.norm_search = e926.norm_search0
        e926.score_threshold = e926.score_threshold0
        return bot.send(event, "成功设置回默认")

    if msg == '<img.e926.local':
        id = None
        if app.is_group_event(event):
            id = event.group.id
        else:
            id = event.sender.id
        return bot.send(event, Seen.local_stastic(id))

    if msg.find('<img.e926.tset ') == 0:
        last = msg[len('<img.e926.tset '):]
        nt = -1
        try:
            nt = int(last.strip())
            if nt < 0:
                raise Exception
            e926.score_threshold_r = nt
        except:
            return bot.send(event, "参数不正确")
        finally:
            return bot.send(event, "成功修改e621.threshold 为" + str(nt))

    if msg.find('<img.e926.pget ') == 0:
        last = msg[len('<img.e926.pget '):]
        id = -1
        try:
            id = int(last.strip())
        except:
            return bot.send(event, "参数错误")
        finally:
            if 0 <= id < len(preset):
                return collect_image(bot, event, preset[id][0])
            else:
                return bot.send(event, "参数过大或过小")

    if msg == '<img.e926.preset':
        return bot.send(event, '\n'.join([str(a) + ':   ' + preset[a][0] + '  ---- ' + preset[a][1]
                                          for a in range(len(preset))]))

