import time
from mirai import GroupMessage, FriendMessage
from pixiv import pixiv

import sys
sys.path.append('..')
from utils import ImgDataStore
from utils import VisStore


IllustBuffer: ImgDataStore.ImageData
SearchBuffer: ImgDataStore.ImageData
VisData: VisStore.SeenPicture
IllustIntroBuffer: ImgDataStore.ImageData
UserEnumIllustsBuffer: ImgDataStore.ImageData


PAGE_REFRESH_TIME = 600     # 10min
ILLUST_REFRESH_TIME = 600   # 10min
ENUM_ILLUST_FRESH_TIME = 480    # 8min


def on_init():
    global IllustBuffer, SearchBuffer, VisData, IllustIntroBuffer, UserEnumIllustsBuffer
    IllustBuffer = ImgDataStore.ImageData("pixiv/IllustPage.json")
    SearchBuffer = ImgDataStore.ImageData("pixiv/FirstPage.json")
    VisData = VisStore.SeenPicture('imgs/pixiv.json')

    IllustIntroBuffer = ImgDataStore.ImageData("pixiv/IllustIntro.json")
    UserEnumIllustsBuffer = ImgDataStore.ImageData('pixiv/UserEnumIllusts.json')


def has_search_buffer(search, page):
    search = search + '#%d' % page
    if not SearchBuffer.has(search):
        return None
    if time.time() - SearchBuffer.get_data()[search]['time'] > PAGE_REFRESH_TIME:
        return None
    return SearchBuffer.get_data()[search]['data']


def save_search_buffer(search, page, data):
    search = search + '#%d'%page
    SearchBuffer.add(search, {'time': time.time(),
                              'data': data})


def get_event_id(event):
    if type(event) is GroupMessage:
        # event = GroupMessage(event)
        return event.group.id
    if type(event) is FriendMessage:
        # event = FriendMessage(event)
        return event.sender.id
    raise ValueError("this event isn't we want")


def bondage_with_seen(illusts, event):
    fid = get_event_id(event)
    ret = []
    for a in illusts:
        ret.append((VisData.seen_count(fid, a['id']), a))
    return ret


def filter_over_pages(illusts, threleq):
    ret = []
    for i in illusts:
        if i['pageCount'] <= threleq:
            ret.append(i)
    return ret


def have_intro_buffer(id):
    id = str(id)
    if not IllustIntroBuffer.has(id):
        return False
    if time.time() - IllustIntroBuffer.get_data()[id]['time'] > ILLUST_REFRESH_TIME:
        return False
    return True


def get_intro_buffer(id):
    return IllustIntroBuffer.get_data()[str(id)]['data']


def save_intro_buffer(id, intro):
    IllustIntroBuffer.add(str(id), {
        'time': time.time(),
        'data': intro
    })


async def adaptive_get_intro(pid):
    if have_intro_buffer(pid):
        return get_intro_buffer(pid)
    url = pixiv.make_illust_info_page(pid)
    resp = await pixiv.async_get(url)
    if resp.status_code != 200:
        raise ValueError("not a good code " + str(resp.status_code))
    dat = resp.json()
    save_intro_buffer(pid, dat['body'])
    return dat['body']


async def adaptive_get_user_enum_illusts(uid):
    global UserEnumIllustsBuffer, ENUM_ILLUST_FRESH_TIME
    uid = str(uid)
    if UserEnumIllustsBuffer.has(uid):
        if time.time() - UserEnumIllustsBuffer.get(uid)['time'] <= ENUM_ILLUST_FRESH_TIME:
            return UserEnumIllustsBuffer.get(uid)['data']
    url = pixiv.make_user_illusts_enum_url(uid)
    resp = await pixiv.async_get(url)
    if resp.status_code != 200:
        raise ValueError("not a good code " + str(resp.status_code))
    dat = resp.json()
    UserEnumIllustsBuffer.add(uid, {
        'time': time.time(),
        'data': dat
    })
    return dat

