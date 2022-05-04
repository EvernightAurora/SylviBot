from utils import SubscribeCore, ParseOrder, ImgDataStore, YoutubeCore, ErrorSend
import asyncio
from utils.WaitLock import SendLock
from Proc import HelpProc
from mirai.models.message import Image, Plain
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from mirai import Mirai, GroupMessage, FriendMessage
import cv2
from utils import JsonStore, configLoader
import random

doc = [
    ['<subscribers.youtube.checkauthor id', '查询指定id的作者是否存在'],
    ['<subscribers.youtube.onofflink', '切换本群是否解析youtube链接'],
    ['<subscribers.youtube.add id', '订阅这个']
]

OnList: JsonStore.JsonStore
SubscriberSeen: ImgDataStore.ImageData
YoutubeSchedule: AsyncIOScheduler
SCHEUDLE_MINUTES = 6


async def on_check_author(bot: Mirai, event, who):
    v_url = 'https://www.youtube.com/channel/%s/videos' % who
    res = await YoutubeCore.is_url_exists(v_url)
    if res is None:
        await bot.send(event, 'qwq')
        await ErrorSend.send_error_async(bot)
        return
    elif not res:
        await bot.send(event, '该id指定的作者不存在uwu', quote=True)
        return

    @ErrorSend.attempt_moving(bot)
    async def vd():
        id, header, subscribers = await YoutubeCore.adaptive_get_id_header_subscribers(who)
        h_path = await YoutubeCore.download_image(header, id, True)
        i = cv2.imread(h_path)
        cv2.imwrite(h_path, i)
        chain = [Image(path=h_path), '\n' + id + '\n', subscribers]
        await bot.send(event, chain, quote=True)

    await vd()
    return


async def on_reply_url(bot: Mirai, event, url0):
    print('extracted ' + url0)
    if not await YoutubeCore.is_url_exists(url0):
        await bot.send(event, '链接404啦')
        return

    @ErrorSend.attempt_moving(bot)
    async def vd():
        dit = await YoutubeCore.get_video_data(url0)
        id = dit['id']
        t_url = dit['thumbnail']
        thumb_path = await YoutubeCore.download_image(t_url, id)
        if len(dit['describe']) > 128:
            dit['describe'] = dit['describe'][:128] + '\n...'
        chain = [dit['title'], Image(path=thumb_path), '\n作者:' + dit['author'] + '\n作者id:%s\n' % dit['authorId'],
                 '描述:' + dit['describe'] + '\n', '时长:%ss, 播放量:%s' % (dit['lens'], dit['view'])]
        return chain

    chain = await vd()
    if not chain:
        await bot.send(event, '出了点问题pwp')
        return
    await bot.send(event, chain)


async def _get_user_most_recent_video(bot: Mirai, event, uid):
    lists = await YoutubeCore.adaptive_get_user_recent_videos(uid)
    print('in summary %d in list' % len(lists))
    one = lists[0]
    title = YoutubeCore.get_video_title(one)
    pub = YoutubeCore.get_publish_time_almost(one)
    thumb_img = YoutubeCore.get_thumbnails_large(one)
    vid = YoutubeCore.get_video_id(one)
    img = await YoutubeCore.download_image(thumb_img, vid)
    chain = [title + '\n', Image(path=img), '发布时间(分钟级误差): %s\n' % pub, '视频链接: https://www.youtube.com/watch?v=' + vid]
    await bot.send(event, chain)


def root_proc(bot: Mirai, event, msg):
    result, last = ParseOrder.detect_order(msg, '<subscribers.youtube.test', 1)
    if result:
        return _get_user_most_recent_video(bot, event, last[0])


########################## of subscribe ####################3
# arg: [ytb_name, ytb_id, task-id]
CLASS_NAME = 'youtube_subscriber'


def make_taskid(fid, seekid):
    return fid + '-' + seekid


async def sign_func(bot: Mirai, fid, args):
    target = await SubscribeCore.get_sender(bot, fid)
    ytb_name = args[0]
    yid = args[1]
    task_id = args[2]
    print('%s 订阅了了 %s（%s)的视频' % (fid, ytb_name, yid))
    global SubscriberSeen, YoutubeSchedule

    @YoutubeSchedule.scheduled_job('interval', minutes=SCHEUDLE_MINUTES, seconds=random.randint(0, 59),
                                   id=task_id, timezone='Asia/Shanghai', max_instances=4)
    async def youtube_func():
        saw = SubscriberSeen.get(task_id)
        lists = await YoutubeCore.adaptive_get_user_recent_videos(yid)
        for one in lists[:25]:
            this_id = YoutubeCore.get_video_id(one)
            if this_id not in saw.keys():
                title = YoutubeCore.get_video_title(one)
                header_ = YoutubeCore.get_thumbnails_large(one)
                time_ = YoutubeCore.get_publish_time_almost(one)
                make_url = 'https://www.youtube.com/watch?v=' + this_id
                header = await YoutubeCore.download_image(header_, this_id)
                chain = ['群订阅的 %s 发布新视频啦\n' % ytb_name,
                         title,
                         Image(path=header),
                         '发布时间(分钟级误差): %s\n' % time_,
                         '网址: ' + make_url]
                await bot.send(target, chain)
                SubscriberSeen.get(task_id)[this_id] = 0
                SubscriberSeen.flush()


async def logout_func(bot: Mirai, fid, args):
    task_id = args[2]
    ytb_name = args[0]
    global SubscriberSeen, YoutubeSchedule
    YoutubeSchedule.remove_job(job_id=task_id)
    print('%s 取消了 订阅%s的视频' % (fid, ytb_name))
    SubscriberSeen.remove(task_id)
    SubscriberSeen.flush()


helper_doc_0 = '''
<订阅youtube作者
用法: <订阅youtube作者 <作者id>
按照id订阅youtube作者，会将新发布的作品提示到群内
用例: <订阅youtube作者 UC_SI1j1d8vJo_rYMV5o_dRg
'''

helper_doc_1 = '''
<检测youtube作者
用法: <检测youtube作者 <作者id>
检测id是不是youtuber上一个该有人的id
用例: <检测youtube作者 UC_5I3JXuAX8ykQRvr4KV1Nw
'''


def on_init():
    global OnList, SubscriberSeen, CLASS_NAME, YoutubeSchedule
    OnList = JsonStore.JsonStore('data/subscribe/youtube/on_off_list.json')
    SubscriberSeen = ImgDataStore.ImageData('data/subscribe/youtube/AllSeen.json')
    YoutubeCore.on_init()
    SubscribeCore.register_type(CLASS_NAME, sign_func, logout_func, '订阅youtube的视频哦~')
    YoutubeSchedule = AsyncIOScheduler()
    HelpProc.register_helper(['<订阅youtube作者'], helper_doc_0)
    HelpProc.register_helper(['<检测youtube作者'], helper_doc_1)


async def on_startup(_):
    global YoutubeSchedule
    YoutubeSchedule.start()


async def on_shutdown(_):
    global YoutubeSchedule
    YoutubeSchedule.shutdown()


async def make_subscribe(bot: Mirai, event, who):
    global SubscriberSeen, CLASS_NAME
    v_url = 'https://www.youtube.com/channel/%s/videos' % who
    fid = SubscribeCore.get_event_fid(event)
    task_id = make_taskid(fid, who)
    if SubscriberSeen.has(task_id):
        await bot.send(event, '已经订阅这位啦')
        return
    res = await YoutubeCore.is_url_exists(v_url)
    if res is None:
        await bot.send(event, '网络出现了点问题qwq, 或者不存在指定的作者id')
        return
    if not res:
        await bot.send(event, 'uwu不存在作者id:' + who)
        return

    @ErrorSend.attempt_moving(bot)
    async def get():
        dit = await YoutubeCore.adaptive_get_id_header_subscribers(who)
        if not dit:
            raise ValueError('this is a error')
        id, header_url, subs = dit
        header = await YoutubeCore.download_image(header_url, id, refresh=True)
        video_list = await YoutubeCore.adaptive_get_user_recent_videos(who)
        video_id_list = [YoutubeCore.get_video_id(i) for i in video_list]
        return id, header, subs, video_id_list

    dit = await get()
    if not dit:
        await bot.send(event, '得到用户失败uwu')
    id, header, subs, vlist = dit
    SubscriberSeen.add(task_id, {i: 0 for i in vlist})
    SubscriberSeen.flush()
    describe = '订阅了油管 %s (id=%s)的所有视频' % (id, who)
    args = [id, who, task_id]
    await SubscribeCore.runtime_login(fid, describe, CLASS_NAME, args)
    chain = ['已成功订阅%s (id:%s)的所有视频' % (id, who),
             Image(path=header),
             '\n' + subs + '\n',
             'https://www.youtube.com/channel/' + who]
    await bot.send(event, chain)
    for qq in configLoader.get_config('root_qq', []):
        await bot.send(await bot.get_friend(qq), [fid + ' 订阅了 \n'] + chain)


def proc(bot: Mirai, event, msg):
    result, last = ParseOrder.detect_order(msg, '<subscribers.youtube.checkauthor', 1)
    if result:
        return on_check_author(bot, event, last[0])

    result, _ = ParseOrder.detect_order(msg, '<subscribers.youtube.onofflink')
    if result:
        fid = SubscribeCore.get_event_fid(event)
        if fid in OnList.get_data().keys():
            OnList.get_data().pop(fid)
        else:
            OnList.get_data()[fid] = 0
        OnList.flush()
        if fid in OnList.get_data().keys():
            return bot.send(event, '成功开启youtube链接解析')
        else:
            return bot.send(event, '成功关闭youtube链接解析')

    result, last = ParseOrder.detect_order(msg, '<subscribers.youtube.add', 1)
    if result:
        return make_subscribe(bot, event, last[0])

    if type(event) is GroupMessage and SubscribeCore.get_event_fid(event) not in OnList.get_data().keys():
        return None

    text = ''
    for i in event.message_chain:
        if type(i) is Plain:
            text += ' ' + str(i).strip()
    text = text.strip()
    url0 = YoutubeCore.has_video_url(text)
    if url0:
        return on_reply_url(bot, event, url0)

