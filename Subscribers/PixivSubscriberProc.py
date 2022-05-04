from utils import SubscribeCore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from mirai import Mirai
from utils import ParseOrder
import time
import os
from utils import JsonStore
from utils import ErrorSend
from pixiv import pixivBuffer, pixiv
from mirai.models.message import Image
from utils import Access, configLoader
import random
import asyncio
from utils.WaitLock import SendLock
from Proc import HelpProc
from pixiv import pixivGIF
from pixiv import DownloadLock


# args: [taskid, uid, mode:[all, safe], uname]
TYPE_NAME = 'pixiv_subscriber'
SeenFileDict = {}
pixiv_scheduler: AsyncIOScheduler
SCHEDULED_INTERVAL_MINUTES = 4
break_interval = .5
P_Subscribe_lock = SendLock(overtime=20)
Query_Lock = SendLock(overtime=3.)
download_lock = DownloadLock.DownloadingLock()

helper_doc_0 = '''
<订阅p站作者
用法: <订阅p站作者 <1个或更多作者的pid>
订阅这些作者，在它们发布新作品的时候，将图片搬运到本群~
对于全年龄还是仅safe，将自动按照群断定
显示所有订阅以及取消订阅参考 <所有订阅  <取消订阅 两个命令
用例: <订阅p站作者 65599927 67489092
'''


def make_task_id(fid, uid):
    return str(fid) + '-' + str(uid)


def get_seen_file_path(fid, uid):
    task_id = make_task_id(fid, uid)
    return os.path.join('data/subscribe/pixiv', task_id)


async def stable_get_user_enum(bot, uid, attempts=5):
    attempt = 0
    while True:
        try:
            ret = await pixivBuffer.adaptive_get_user_enum_illusts(uid)
            if not ret:
                raise ValueError("ret cannot be 0")
            return ret
        except:
            attempt += 1
            if attempt > attempts:
                await ErrorSend.send_error_async(bot, attempt)
                return None


async def stable_get_illust_info(bot, pid, attempts=5):
    attempt = 0
    while True:
        try:
            ret = await pixivBuffer.adaptive_get_intro(pid)
            if not ret:
                raise ValueError("ret cannot be 0")
            return ret
        except:
            attempt += 1
            if attempt > attempts:
                await ErrorSend.send_error_async(bot, attempt)
                return None


async def stable_download_illust(bot, pid, attempts=5):
    attempt = 0
    with await download_lock.locking(key=pid):
        while True:
            try:
                dat = await stable_get_illust_info(bot, pid, attempts)
                if not dat:
                    return None
                if pixivGIF.is_gif(dat):
                    img_path = await pixivGIF.download_gif(pid, origin=True)
                    if not img_path:
                        raise ValueError('img path is none')
                    return Image(path=img_path)
                else:
                    ret = await pixiv.download_illust_async_ex(pid, 20, True)
                    if not ret:
                        raise ValueError("ret cannot be 0")
                    return ret
            except:
                attempt += 1
                if attempt > attempts:
                    await ErrorSend.send_error_async(bot, attempt)
                    return None


async def on_login(bot: Mirai, fid, args):
    global SeenFileDict, SCHEDULED_INTERVAL_MINUTES, pixiv_scheduler, Query_Lock
    task_id = args[0]
    uid = args[1]
    mode = args[2]
    name = args[3]

    f_dir = get_seen_file_path(fid, uid)

    SeenFileDict[task_id] = JsonStore.JsonStore(f_dir)

    @pixiv_scheduler.scheduled_job('interval', minutes=SCHEDULED_INTERVAL_MINUTES, seconds=random.randint(0, 59),
                                   id=task_id, timezone='Asia/Shanghai', max_instances=10)
    async def look_research_pixiv():
        seen = SeenFileDict[task_id]
        seen: JsonStore.JsonStore
        with await Query_Lock.locking():
            enums = await stable_get_user_enum(bot, uid)
        if not enums:
            return
        enums = enums['body']['illusts'].keys()
        lasts = [i for i in enums if i not in seen.get_data().keys()]
        lasts = sorted(lasts)
        target = await SubscribeCore.get_sender(bot, fid)
        for pid in lasts:
            chain = ["订阅的作者: %s[uid=%s]发布了新作品\n" % (name, str(uid))]
            intro = await stable_get_illust_info(bot, pid)
            if not intro:
                continue
            if 'body' in intro.keys():
                intro = intro['body']
            if mode != 'all':
                if pixiv.is_info_r18_2(intro):
                    chain.append('不过似乎是不太适合在这里发的内容qwq\n作品id: %s' % str(pid))
                    await bot.send(target, chain)
                    seen.get_data()[pid] = 0
                    seen.flush()
                    continue
            imgs = await stable_download_illust(bot, pid)
            if not imgs:
                continue
            chain.extend(imgs)
            update = intro['updateDate'] if 'updateDate' in intro.keys() else intro['uploadDate']
            chain.append("\n" + intro['title'] + "\npid: " + str(pid) + "  作者: " + intro['userName'] +
                         "\n上传日期: " + pixiv.trans_localtime(update))
            seen.get_data()[pid] = 0
            seen.flush()
            await bot.send(target, chain)
    print(fid + ' 订阅了p站的%s[%s]的%s图片' % (name, uid, mode))


async def on_logout(bot: Mirai, fid, args):
    global SeenFileDict, pixiv_scheduler
    task_id = args[0]
    uid = args[1]
    f_dir = get_seen_file_path(fid, uid)
    if os.path.isfile(f_dir):
        os.remove(f_dir)
    pixiv_scheduler.remove_job(job_id=task_id)
    print(fid + ' 不再订阅 ' + args[3])
    SeenFileDict.pop(task_id)


def on_init():
    global pixiv_scheduler, TYPE_NAME
    pixiv_scheduler = AsyncIOScheduler()
    SubscribeCore.register_type(TYPE_NAME, on_login, on_logout, '订阅p站的作者哦')
    HelpProc.register_helper(['<订阅p站作者'], helper_doc_0)


async def on_startup(_):
    global pixiv_scheduler
    pixiv_scheduler.start()


async def on_shutdown(_):
    global pixiv_scheduler
    pixiv_scheduler.shutdown()


async def stable_get_async(bot, url, attempts=5):
    local_attempt = 0
    while True:
        try:
            resp = await pixiv.async_get(url)
            if not resp:
                raise ValueError
            return resp
        except:
            local_attempt += 1
            if local_attempt > attempts:
                await ErrorSend.send_error_async(bot, local_attempt)
                return None


async def stable_get_image(bot, url, todir, attempts=5):
    local_attempt = 0
    while True:
        try:
            resp = await pixiv.async_download_image(url, todir)
            if not resp:
                raise ValueError
            return resp
        except:
            local_attempt += 1
            if local_attempt > attempts:
                await ErrorSend.send_error_async(bot, local_attempt)
                return None


async def stable_get_uner_infos(bot, uid):
    url = pixiv.make_user_query_url(uid)
    resp = await stable_get_async(bot, url)
    if not resp:
        return None
    resp = resp.json()['body']
    name = resp['name']
    imgurl = resp['imageBig']
    comment = resp['comment']

    save_dir = os.path.join('pixiv/headers/', os.path.split(imgurl)[-1])
    ret0 = await stable_get_image(bot, imgurl, save_dir)
    if not ret0:
        return None
    return name, save_dir, comment


async def stable_get_uner_infos_little(bot, uid):
    url = pixiv.make_user_query_url(uid)
    resp = await stable_get_async(bot, url)
    if not resp:
        return None
    resp = resp.json()['body']
    name = resp['name']
    imgurl = resp['image']
    comment = resp['comment']

    save_dir = os.path.join('pixiv/headers/', os.path.split(imgurl)[-1])
    ret0 = await stable_get_image(bot, imgurl, save_dir)
    if not ret0:
        return None
    return name, save_dir, comment


async def subscribe_pixiv(bot: Mirai, fid, uid, mode):
    global TYPE_NAME, P_Subscribe_lock
    with await P_Subscribe_lock.locking():
        Key = await P_Subscribe_lock.wait_lock()
        if mode not in ['safe', 'all']:
            raise ValueError("not a proper mode")

        target = await SubscribeCore.get_sender(bot, fid)
        global SeenFileDict
        if make_task_id(fid, uid) in SeenFileDict.keys():
            await bot.send(target, '已经订阅这个作者啦uwu')
            return
        try:
            u0 = int(uid)
        except ValueError:
            await bot.send(target, '必须指定作者id~')
            return

        ret_arg = await stable_get_uner_infos(bot, uid)
        if not ret_arg:
            await bot.send(target, '得到作者信息失败qwq')
            return
        name, save_dir, comment = ret_arg

        args = [make_task_id(fid, uid), uid, mode, name]

        enums = await stable_get_user_enum(bot, uid)
        if not enums:
            await bot.send(target, '得到作品失败qwq')
            return
        f_n = get_seen_file_path(fid, uid)
        nf = JsonStore.JsonStore(f_n)
        nf.set_data(enums['body']['illusts'])
        nf.flush()
        SeenFileDict[make_task_id(fid, uid)] = nf
        await SubscribeCore.runtime_login(fid, '订阅了p站作者%s[%s]的%s图片' %
                                          (name, str(uid), "所有" if mode == 'all' else '全年龄'), TYPE_NAME, args)
        chain = ['已成功订阅作者%s的%s图片\nuid=%s' % (name, mode, uid), Image(path=save_dir), comment]
        await bot.send(target, chain)
        for qq in configLoader.get_config('root_qq', []):
            await bot.send(await bot.get_friend(qq), [fid + ' 订阅了 \n'] + chain)


async def subscribe_pixiv_s(bot: Mirai, fid, uids, mode):
    global TYPE_NAME, P_Subscribe_lock
    if mode not in ['safe', 'all']:
        raise ValueError("not a proper mode")
    with await P_Subscribe_lock.locking():
        target = await SubscribeCore.get_sender(bot, fid)
        try:
            for uid in uids:
                u0 = int(uid)
        except ValueError:
            await bot.send(target, '只能指定作者的id~')
            return

        qwqs = []
        pwps = []
        global SeenFileDict
        for uid in uids:
            if make_task_id(fid, uid) in SeenFileDict.keys():
                qwqs.append(uid)
            else:
                pwps.append(uid)
        if qwqs:
            await bot.send(target, '已经订阅[%s]这些作者啦uwu' % (','.join(qwqs)))
        pwps = list(set(pwps))
        uids = pwps
        if not uids:
            await bot.send(target, '这里面没有还没订阅的作者了w')
            return

        ret_args = []  # uid, name, save_dir, comment, describe, args
        for uid in uids:
            ret_arg = await stable_get_uner_infos(bot, uid)
            if not ret_arg:
                await bot.send(target, '得到作者信息失败qwq')
                return
            name, save_dir, comment = ret_arg

            args = [make_task_id(fid, uid), uid, mode, name]

            enums = await stable_get_user_enum(bot, uid)
            if not enums:
                await bot.send(target, '得到作品失败qwq')
                return
            f_n = get_seen_file_path(fid, uid)
            nf = JsonStore.JsonStore(f_n)
            nf.set_data(enums['body']['illusts'])
            nf.flush()
            describe = '订阅了p站作者%s[%s]的%s图片' % (name, str(uid), "所有" if mode == 'all' else '全年龄')
            ret_args.append((uid, name, save_dir, comment, describe, args))
        chains = ['已成功订阅%d个作者的%s图片:\n' % (len(ret_args), mode)]
        for uid, name, save_dir, comment, describe, args in ret_args:
            await SubscribeCore.runtime_login(fid, describe, TYPE_NAME, args)
            chains.extend([Image(path=save_dir), '作者%s[%s]' % (name, uid)])
        await bot.send(target, chains)
        for qq in configLoader.get_config('root_qq', []):
            await bot.send(await bot.get_friend(qq), [fid + ' 订阅了 \n'] + chains)


doc = [
    ['<subscribers.pixiv.login_safe uid', '订阅作者的安全图'],
    ['<subscribers.pixiv.login_all uid', '订阅作者的全部图，是不是全部还得看群']
]


def proc(bot: Mirai, event, msg):
    result, last = ParseOrder.detect_order(msg, '<subscribers.pixiv.login_safe', 1)
    if result:
        uid = last[0]
        fid = SubscribeCore.get_event_fid(event)
        return subscribe_pixiv(bot, fid, uid, 'safe')

    result, last = ParseOrder.detect_order(msg, '<subscribers.pixiv.login_all', range(1, 100))
    if result:
        mode = 'all'
        if not Access.can_access(event):
            mode = 'safe'
        fid = SubscribeCore.get_event_fid(event)
        if len(last) == 1:
            uid = last[0]
            return subscribe_pixiv(bot, fid, uid, mode)
        else:
            return subscribe_pixiv_s(bot, fid, last, mode)

