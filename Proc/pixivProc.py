import mirai.models.message
from pixiv import pixiv
from utils.WaitLock import global_wait as Wait
from utils import ParseOrder, Access
from pixiv import pixivBuffer
from pixiv import pixivParser, pixivGIF
from utils import ErrorSend
from mirai import Mirai
from Proc import HelpProc
import asyncio
from mirai.models.message import At
from mirai import GroupMessage, FriendMessage

doc = [
    ['<img.pixiv.getsafe( sth)', '通过p站搜索'],
    ['<img.pixiv.getr18( sth)', '通过p站搜索涩涩'],
    ['<img.pixiv.get( sth)', '通过p站搜索可能有涩涩的图'],
    ['<img.pixiv.searchhelp', '得到搜索文档'],
    ['<img.pixiv.searchuser .', '查询用户'],
    ['<img.pixiv.default', '得到当前默认搜素']
]

MAX_SEARCH_CNT = 8

helper_doc_0 = '''
<来点清水， <来点涩涩， <来点康康
用法 <来点清水 (+参数)
均为实时从p站上获取作品，默认过滤掉订阅<250的作品
若无参数，则默认是搜索伊布
支持一些特殊参数
    订阅限制:   订阅大于:500
    作者:     作者:(作者的p站数字id)， 由于p站限制，指定作者时，大部分特殊搜索不再适用（如收藏限制），同时也只能指定最多一个tag
    指定作品:   id:(pid)
对于作者的id,可通过<查询p站作者 命令来找到
tips:
    p站无法通过搜索作者名来搜到作者作品
    由于p站是日本网站，对于中文不太支持，所以尽量查询日文
        对于宝可梦日文名的查询可以用<查询 命令
'''

helper_doc_1 = '''
<查询p站作者
用法: <查询p站作者 <查询词>
在p站上按照名字查找作者，并返回前几条的头像、名字、介绍还有pid
可以帮助你通过<来点清水 中指定作者的pid来查找作者的图
'''


def on_init():
    pixivBuffer.on_init()
    pixiv.on_init()
    pixivGIF.on_init()
    HelpProc.register_helper(['<来点清水', '<来点涩涩', '<来点康康'], helper_doc_0)
    HelpProc.register_helper(['<查询p站作者'], helper_doc_1)


async def on_search_user(bot: Mirai, event, last):
    last = last.strip()
    try:
        list = await pixiv.search_user_async(last)
        if type(list) is str:
            await bot.send(event, list, quote=True)
            return
        if not list:
            await bot.send(event, "查找用户出了点错uwu", quote=True)
            await ErrorSend.send_error_async(bot)
            return
        chain = ["查询用户结果\n"]
        pixivParser.last_search = []
        for user in list:
            if len(pixivParser.last_search) >= MAX_SEARCH_CNT:
                break
            imgp = await pixiv.download_user_header_async(user)
            if imgp:
                chain.append(mirai.models.message.Image(path=imgp))
            else:
                chain.append("(此处应有头像)")
            chain.append("[%d] %s [pid=%s]\n简介: %s\n\n" %
                         (len(pixivParser.last_search), user['name'], str(user['id']), user['description']))
            pixivParser.last_search.append(user['id'])
        await bot.send(event, chain, quote=True)
    except:
        await bot.send(event, "出了一点问题qwq", quote=True)
        await ErrorSend.send_error_async(bot)


def get_image(bot, event, Search, mode='safe'):
    print('start find pixiv ' + Search)
    if not Search:
        Search = '伊布家族'
    try:
        res, dat = pixiv.get_illustid(event, search=Search, mode=mode)
    except:
        async def f0():
            await bot.send(event, '查找出现了点问题uwu')
            await ErrorSend.send_error_async(bot)

        return f0()
    if not res:
        return bot.send(event, dat)
    msg = []
    msg.append("共%d个结果\n" % dat[0])
    pid = dat[1]['id']
    chain = pixiv.download_illust(pid, dat[2])
    if not chain:
        print('下载出问题了qwq')

        async def f1():
            await bot.send(event, "下载出了点问题qwq")
            await ErrorSend.send_error_async(bot)

        return f1()
    msg.extend(chain)
    id = pixivBuffer.get_event_id(event)
    pixivBuffer.VisData.saw_again(id, pid)
    msg.append("\n" + dat[1]['title'] + "\npid: " + str(pid) + "  作者: " + dat[1]['userName'] +
               "\n上传日期: " + dat[1]['updateDate'] + '\n这是第%d次看' % (pixivBuffer.VisData.seen_count(id, pid)))
    print('完成！')
    return bot.send(event, msg)


async def get_image_async(bot: Mirai, event, Search, mode='safe', attemp=5, attemp_interval=1):
    print('start find pixiv ' + Search + ' at ' + mode)
    if not Search:
        Search = ''
    local_attemp = 0
    while True:
        try:
            res, dat = await pixiv.get_illustid_async(event, search=Search, mode=mode)
            break
        except:
            local_attemp += 1
            print('查找出错啦')
            if local_attemp > attemp:
                await ErrorSend.send_error_async(bot, attempt=local_attemp)
                await bot.send(event, '查找出现了错误qwq', quote=True)
                return
            await asyncio.sleep(attemp_interval)
    if not res:
        await bot.send(event, dat)
        # await ErrorSend.send_error_async(bot)
        return
    msg = []
    msg.append("共%d个结果\n" % dat[0])
    id = pixivBuffer.get_event_id(event)
    pid = dat[1]['id']
    pixivBuffer.VisData.saw_again(id, pid)
    if pixivGIF.is_gif(dat[1]):
        loc_attemp = 0
        while True:
            try:
                img_path = await pixivGIF.download_gif(pid, origin=dat[3])
                if not img_path:
                    raise ValueError('img path is none')
            except:
                loc_attemp += 1
                print(str(loc_attemp) + ' 下载gif出问题了')
                if loc_attemp > attemp:
                    await ErrorSend.send_error_async(bot, attempt=loc_attemp)
                    await bot.send(event, '下载gif出了点问题pwp', quote=True)
                    return
                await asyncio.sleep(attemp_interval)
                continue
            break
        msg.append(mirai.models.message.Image(path=img_path))
    else:
        local_attemp = 0
        while True:
            chain = await pixiv.download_illust_async_ex(pid, dat[2], origin=dat[3])
            if not chain:
                local_attemp += 1
                print(str(local_attemp) + ' 下载出问题了qwq')
                if local_attemp > attemp:
                    await ErrorSend.send_error_async(bot, attempt=local_attemp)
                    await bot.send(event, "下载出了点问题qwq", quote=True)
                    return
                await asyncio.sleep(attemp_interval)
                continue
            break
        msg.extend(chain)
    update = dat[1]['updateDate'] if 'updateDate' in dat[1].keys() else dat[1]['uploadDate']
    msg.append("\n" + dat[1]['title'] + "\npid: " + str(pid) + "  作者: " + dat[1]['userName'] +
               "\n上传日期: " + pixiv.trans_localtime(update)[:10] +
               '\n这是第%d次看' % (pixivBuffer.VisData.seen_count(id, pid)))
    print('完成！')
    Key = await Wait.wait_lock()
    try:
        await bot.send(event, msg, quote=True)
    except:
        await bot.send(event, "pid: %s\n发送失败qwq 可能是图片太大或有问题" % (str(pid)), quote=True)
        return
    Wait.unlock(Key)
    return


def root_proc(bot: mirai, event, msg: str):
    return None


def proc(bot: mirai, event, msg: str):
    fromid = pixivBuffer.get_event_id(event)

    result, lasts = ParseOrder.detect_order(msg, '<img.pixiv.getsafe', list(range(100)))
    if result:
        if lasts:
            if 'r-18' in lasts or 'r18' in lasts or 'R18' in lasts or 'R-18' in lasts:
                return bot.send(event, '不要涩涩嘛qwq', quote=True)
        if lasts:
            Search = ' '.join(lasts)
        else:
            Search = ''
        return get_image_async(bot, event, Search, 'safe')

    result, lasts = ParseOrder.detect_order(msg, '<img.pixiv.getr18', list(range(100)))
    if result:
        if not Access.can_access(event):
            return bot.send(event, "涩涩不可以！", quote=True)
        if lasts:
            Search = ' '.join(lasts)
        else:
            Search = ''
        return get_image_async(bot, event, Search, 'r18')

    result, lasts = ParseOrder.detect_order(msg, '<img.pixiv.get', list(range(100)))
    if result:
        mode = 'all'
        if not Access.can_access(event):
            mode = 'safe'
        if lasts:
            Search = ' '.join(lasts)
        else:
            Search = ''
        return get_image_async(bot, event, Search, mode)

    result, _ = ParseOrder.detect_order(msg, '<img.pixiv.default')
    if result:
        return bot.send(event, '目前pixiv默认搜索是\n' + pixiv.DEFAULT_SEARCH)

    result, _ = ParseOrder.detect_order(msg, '<img.pixiv.searchhelp')
    if result:
        return bot.send(event, pixivParser.make_doc())
    result, last = ParseOrder.detect_order(msg, '<img.pixiv.searchuser', list(range(1, 100)))
    if result:
        back = msg[len('<img.pixiv.searchuser '):]
        return on_search_user(bot, event, back)
    return None
