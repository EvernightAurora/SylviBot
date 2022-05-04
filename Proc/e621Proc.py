from mirai.models.message import MessageChain
from utils import e926
import mirai.models.message
from utils import VisStore, Access
import app
from utils.WaitLock import global_wait as Wait
from Proc import HelpProc


Seen: VisStore.SeenPicture


helper_doc_0 = '''
命令： <来点w
用法: <来点w (+关键词们)
从e621上按照给定的关键词随机找图~
如果无参数(<来点w)默认是伊布图
默认过滤掉favcount<350的作品
支持e621的一些特殊搜索，例如
    指定id——  id:1234567
    指定favcount，这会覆盖默认—— favcount:>0
    排除关键词—— 关键词前加-
样例: 
    如果想搜索favcount>1000的没有唯一王的伊布图
    <来点w eeveelution favcount:>1000 -flareon
tips:
    e621是欧美的，所以关键词必须是英文的
'''


def on_init():
    global Seen
    Seen = VisStore.SeenPicture('imgs/e621.json')
    HelpProc.register_helper(['<来点w'], helper_doc_0)
    e926.on_init()


doc = [
    ['root: <img.e621.dset <...>', '设置默认标签'],
    ['root: <img.e621.clearseen', '清除已看图片'],
    ['<img.e621.tset <int>', '设置阈值,score还是fav视当前情况'],
    ['<img.e621.unset', '设置回默认'],
    ['<img.e621.rget', '随机寻找图片'],
    ['<img.e621.pget <ind>', '搜索给定ind的预设方案'],
    ['<img.e621.get <标签>', '在特定的标签中寻找第一个, 默认有order:random'],
    ['<img.e621.preset', '输出预设方案'],
    ['<img.e621.default', '显示当前随机搜索标签'],
    ['<img.e621.local', '显示一点点本群统计数据'],
    ['<img.e621.scorefav', '修改筛选方式: score还是fav']
]

preset = [
    [e926.norm_search_r0, '伊布'],
    ['alolan_vulpix feral score:>=100', '六尾'],
    ['pokemon score:>=600', '优质（也许）的任意宝可梦'],
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
    if msg == '<img.e621.clearseen':
        id = None
        if app.is_group_event(event):
            id = event.group.id
        else:
            id = event.sender.id
        Seen.clear_seen(id)
        return bot.send(event, '已清除已看过图片数据')

    if msg.find('<img.e621.dset ') == 0:
        last = msg[len('<img.e621.dset '):]
        s = last.strip()
        e926.norm_search_r = s
        return bot.send(event, "成功设置e621.norm_search 为 " + s)


def collect_image(bot, event, key=None):
    if key:
        l = e926.get_searchs_r(key)
    else:
        l = e926.get_searchs_r()
    l = filter_by_seen(event, l)
    if len(l) < 1:
        return bot.send(event, "找不到qaq")
    out = l[0]
    path = e926.download_image_r(out)
    id = None
    if app.is_group_event(event):
        id = event.group.id
    else:
        id = event.sender.id
    Seen.saw_again(id, out['id'])
    print(path + " 好啦w")
    return bot.send(event, MessageChain([
        '来啦w\n',
        mirai.models.message.Image(path=path),
        'score:%d, favor: %d rating:%s  已看过:%d次 链接url:\n%s' %
        (out['score'], out['fav'], out['rating'], Seen.seen_count(id, out['id']), r'https://e621.net/posts/' + out['id'])
    ]))


async def collect_image_async(bot, event, key=None):
    if key:
        l = await e926.get_searchs_r_async(key)
    else:
        l = await e926.get_searchs_r_async()
    l = filter_by_seen(event, l)
    if len(l) < 1:
        a = await bot.send(event, "找不到qaq")
        return a
    print('来找 ' + ('[default]' if not key else key) + ' 啦')
    out = l[0]
    path = await e926.download_image_r_async(out)
    if path is None:
        await bot.send(event, "出了点问题qaq")
        return
    id = None
    if app.is_group_event(event):
        id = event.group.id
    else:
        id = event.sender.id
    Seen.saw_again(id, out['id'])
    print(path + " 好啦w")
    Key = await Wait.wait_lock()
    ret = await bot.send(event, MessageChain([
        '来啦w' + (" 只有%d个图片"%len(l) if len(l) <= 50 else "") + '\n',
        mirai.models.message.Image(path=path),
        'score:%d, favor: %d rating:%s  已看过:%d次 链接url:\n%s' %
        (out['score'], out['fav'], out['rating'], Seen.seen_count(id, out['id']), r'https://e621.net/posts/' + out['id'])
    ]), quote=True)
    Wait.unlock(Key)
    print(('[default]' if not key else key) + ' 找好啦')


def proc(bot, event, msg):
    msg = msg.lower()
    if msg == '<img.e621.rget' or msg == '<img.e621.get':
        if not Access.can_access(event):
            return bot.send(event, "不可以涩涩！")
        print("上好的ero图")
        return collect_image_async(bot, event)

    if msg.find('<img.e621.get ') == 0:
        if not Access.can_access(event):
            return bot.send(event, "不可以涩涩！")
        last = msg[len('<img.e621.get '):]
        last = last.strip()
        print("中好的ero图 " + last)
        return collect_image_async(bot, event, last)

    if msg.find('<img.e621.get+') == 0:
        if not Access.can_access(event):
            return bot.send(event, "不可以涩涩！")
        last = msg[len('<img.e621.get+'):]
        last = last.strip()
        print("好中好的ero图 " + last)
        return collect_image_async(bot, event, e926.norm_search_r + ' ' + last)

    if msg == '<img.e621.default':
        return bot.send(event, "目前e621站的默认搜索: " + e926.norm_search_r +
                        ("\n score阈值: " + str(e926.score_threshold_r) if not e926.USE_FAV else
                         "\n favcount阈值: " + str(e926.favcount_threshold_r)))

    if msg == '<img.e621.scorefav':
        e926.USE_FAV ^= 1
        return bot.send(event, "筛选方式改为" + ("favcount" if e926.USE_FAV else "score"))

    if msg == '<img.e621.unset':
        e926.norm_search_r = e926.norm_search_r0
        e926.score_threshold_r = e926.score_threshold_r0
        e926.favcount_threshold_r = e926.favcount_threshold_r0
        return bot.send(event, "成功设置回默认")

    if msg == '<img.e621.local':
        id = None
        if app.is_group_event(event):
            id = event.group.id
        else:
            id = event.sender.id
        return bot.send(event, Seen.local_stastic(id))

    if msg.find('<img.e621.tset ') == 0:
        last = msg[len('<img.e621.tset '):]
        nt = -1
        try:
            nt = int(last.strip())
            if nt < 0:
                raise Exception
            if e926.USE_FAV:
                e926.favcount_threshold_r = nt
            else:
                e926.score_threshold_r = nt
        except:
            return bot.send(event, "参数不正确")
        else:
            return bot.send(event, "成功修改e621." + ("favcount" if e926.USE_FAV else "score")
                            + "threshold 为" + str(nt))

    if msg.find('<img.e621.pget ') == 0:
        if not Access.can_access(event):
            return bot.send(event, "不可以涩涩！")
        last = msg[len('<img.e621.pget '):]
        id = -1
        try:
            id = int(last.strip())
        except:
            return bot.send(event, "参数错误")
        else:
            if 0 <= id < len(preset):
                return collect_image(bot, event, preset[id][0])
            else:
                return bot.send(event, "参数过大或过小")

    if msg == '<img.e621.preset':
        return bot.send(event, '\n'.join([str(a) + ':   ' + preset[a][0] + '  ---- ' + preset[a][1]
                                          for a in range(len(preset))]))

