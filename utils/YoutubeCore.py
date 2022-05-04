from utils import ClientControl, ErrorSend, ProxySetting, ImgDataStore
from bs4 import BeautifulSoup
import json
import time
from pixiv import pixiv
import os
import requests
from utils import WaitLock
import cv2


Headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/98.0.4758.82 Safari/537.36',
           'accept-language': 'en;q=0.9,zh-CN;q=0.8'
           }

Clients = ClientControl.AsyncClientControl(2, proxies=ProxySetting.Proxy_Set_For_HTTPX, headers=Headers)
UserVideoBuffer: ImgDataStore.ImageData
USER_VIDEO_BUFFER_REFRESH = 120
CallWait = WaitLock.SendLock(overtime=1.)


def on_init():
    global UserVideoBuffer
    UserVideoBuffer = ImgDataStore.ImageData('data/buffer/YoutuberUserVideo.json')


async def get_async(url, b_code=True):
    lk = await CallWait.wait_lock()
    client, key = await Clients.alloc_client()
    resp = await client.get(url, follow_redirects=True)
    Clients.free_client(client, key)

    if b_code:
        if resp.status_code != 200:
            raise ValueError('not a good code ' + str(resp.status_code))
    return resp


async def get_user_raw_data(uid):
    req_url = 'https://www.youtube.com/channel/%s/videos' % uid
    resp = await get_async(req_url)
    resp = resp.text
    pos0 = resp.find('var ytInitialData = ')
    if pos0 < 0:
        raise ValueError('cant find header')
    resp = resp[pos0 + 20:]
    assert resp[0] == '{'
    resp = resp[:resp.find('};') + 1]
    ret = json.loads(resp)
    return ret


async def adaptive_get_user_raw_data(uid):
    if UserVideoBuffer.has(uid):
        if UserVideoBuffer.get(uid)['time'] + USER_VIDEO_BUFFER_REFRESH >= time.time():
            return UserVideoBuffer.get(uid)['data']
    dat = await get_user_raw_data(uid)
    UserVideoBuffer.add(uid, {
        'time': time.time(),
        'data': dat
    })
    return dat


def find_tab(r_json, what):
    tabs = r_json['contents']['twoColumnBrowseResultsRenderer']['tabs']
    for i in tabs:
        if 'tabRenderer' not in i.keys():
            continue
        if i['tabRenderer']['title'] == what:
            return i


async def adaptive_get_user_recent_videos(uid):
    dat = await adaptive_get_user_raw_data(uid)
    videos = find_tab(dat, 'Videos')
    enum = videos['tabRenderer']['content']['sectionListRenderer']['contents']
    enum = enum[0]['itemSectionRenderer']['contents'][0]['gridRenderer']['items']
    return [i for i in enum if 'gridVideoRenderer' in i.keys()]


def get_video_title(vid):
    return vid['gridVideoRenderer']['title']['runs'][0]['text']


def get_video_id(vid):
    return vid['gridVideoRenderer']['videoId']


def get_thumbnails_large(vid):
    return vid['gridVideoRenderer']['thumbnail']['thumbnails'][-1]['url']


def get_publish_time_almost(vid):
    try:
        return vid['gridVideoRenderer']['publishedTimeText']['simpleText']
    except KeyError:
        return '未知时间'


async def is_url_exists(url):

    @ErrorSend.attempt_moving()
    async def local():
        resp = await get_async(url)
        if resp.status_code not in [200, 404]:
            raise Exception('lets try agagin')
        return resp

    res = await local()
    if not res:
        return res
    return res.status_code == 200


async def adaptive_get_id_header_subscribers(uid):
    dat = await adaptive_get_user_raw_data(uid)
    name = dat['header']['c4TabbedHeaderRenderer']['title']
    largest_url = dat['header']['c4TabbedHeaderRenderer']['avatar']['thumbnails'][-1]['url']
    subscribers = dat['header']['c4TabbedHeaderRenderer']['subscriberCountText']['simpleText']
    return name, largest_url, subscribers


async def download_image(url, fid, refresh=False, reopen=True):
    to_file = 'data/buffer/youtube/'
    os.makedirs(to_file) if not os.path.exists(to_file) else None
    to_file += str(fid) + '.jpg'
    if not refresh and os.path.isfile(to_file):
        return to_file
    await pixiv.async_download_image(url, to_file)
    if reopen:
        img = cv2.imread(to_file)
        cv2.imwrite(to_file, img)
    return to_file


def has_video_url(text):
    tex = text.split()
    prefs = [
        'www.youtube.com/watch',
        'm.youtube.com/watch',
        'youtu.be/'
    ]
    url_base = 'https://www.youtube.com/watch?v='
    def extract(s):
        pos = 0
        while len(s) > pos and (str.isalnum(s[pos]) or s[pos] in ['-', '_']):
            pos += 1
        return s[:pos]

    for text in tex:
        for pre in prefs:
            if len(text) > len(pre) and text[:len(pre)] == pre:
                if pre == 'youtu.be/':
                    return url_base + extract(text[len(pre):])
                else:
                    return url_base + extract(text[text.find('v=')+2:])
            s2 = 'https://' + pre
            if len(text) > len(s2) and text[:len(s2)] == s2:
                if pre == 'youtu.be/':
                    return url_base + extract(text[len(s2):])
                else:
                    return url_base + extract(text[text.find('v=')+2:])
    return None


async def get_video_data(vurl):
    ret = dict()
    resp = await get_async(vurl)
    resp = resp.text
    pos0 = resp.find('var ytInitialPlayerResponse = ')
    if pos0 < 0:
        raise Exception("why there havn't this")
    resp = resp[pos0+30:]
    resp = resp[:resp.find('};')+1]
    data = json.loads(resp)
    ret['id'] = data['videoDetails']['videoId']
    ret['title'] = data['videoDetails']['title']
    ret['lens'] = data['videoDetails']['lengthSeconds']
    ret['describe'] = data['videoDetails']['shortDescription']
    ret['thumbnail'] = data['videoDetails']['thumbnail']['thumbnails'][-1]['url']
    ret['author'] = data['videoDetails']['author']
    ret['view'] = data['videoDetails']['viewCount']
    ret['authorId'] = data['videoDetails']['channelId']
    return ret







