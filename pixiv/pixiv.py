import requests
from bs4 import BeautifulSoup
import urllib
from pixiv import pixivBuffer
from pixiv import pixivParser
import asyncio
# import sys
# sys.path.append('..')
from utils import ProxySetting, pixivic
from utils import ClientControl
from utils import e926
import random
import mirai
import os
import cv2
import pytz
import datetime
from utils import configLoader


RATIO_THRESHOLD = 2.2
DEFAULT_SEARCH_PRESET = r'ポケモン (ブイズ OR イーブイ OR ブースター OR シャワーズ OR サンダース OR ' \
                 r'エーフィ OR ブラッキー OR リーフィア OR グレイシア OR ニンフィア) ' \
                 r'-ポケモンごっこ -スカトロ -ポケ擬 -擬人化 '

DEFAULT_SEARCH: str

Headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/98.0.4758.82 Safari/537.36',
           'referer': 'https://www.pixiv.net/tags/',
           'sec-fetch-mode': 'cors',
           'sec-fetch-site': 'same-origin',
           'accepts': 'application/json,*/*',
           'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="98", "Google Chrome";v="98"',
           'sec-fetch-dest': 'empty',
           'sec-ch-ua-platform': '"Windows"',
           'sec-ch-ua-mobile': '?0',
           'accept-encoding': 'gzip, deflate, br',
           'accept-language': 'zh-CN,zh;q=0.9',
           'scheme': 'https'}

Cookies = {'PHPSESSID': '10404525_LjbgApbwIkWB3txThq8vRw3Fx1qLPhhg'}
Sess = requests.session()
Sess.headers = Headers
AsyncClients: ClientControl.AsyncClientControl


def on_init():
    global DEFAULT_SEARCH, Cookies, AsyncClients
    DEFAULT_SEARCH = configLoader.get_config('pixiv_default_search', DEFAULT_SEARCH_PRESET)
    phpsess = configLoader.get_config('pixiv_cookie_PHPSESSID', None)
    if not phpsess:
        Cookies = {}
    else:
        Cookies = {'PHPSESSID': phpsess}
    for i in Cookies.keys():
        Sess.cookies[i] = Cookies[i]
    AsyncClients = ClientControl.AsyncClientControl(4, headers=Headers, cookies=Cookies,
                                                    proxies=ProxySetting.Proxy_Set_For_HTTPX)


def make_query_url(keys, page, type='illust_and_ugoira', mode='all', blt=200, bgt=20000, start_date=None, end_date=None,
                   s_mode='s_tah'):
    keys = urllib.parse.quote(keys)
    ret = "https://www.pixiv.net/ajax/search/artworks/%s?word=%s&order=data_d&" \
          "mode=%s&p=%d&s_mode=%s&type=%s&lang=zh&blt=%d&bgt=%d"\
          % (keys, keys, mode, page, s_mode, type, blt, bgt)
    if start_date:
        start_date = str(start_date)
        start_date = start_date[:4] + '-' + start_date[4:6] + '-' + start_date[6:]
        ret += '&scd=' + start_date
    if end_date:
        end_date = str(end_date)
        end_date = end_date[:4] + '-' + end_date[4:6] + '-' + end_date[6:]
        ret += '&ecd=' + end_date
    return ret


def make_image_url(id):
    return 'https://www.pixiv.net/ajax/illust/' + str(id) + '/pages?lang=zh'


def sync_get(url):
    return Sess.get(url, proxies=ProxySetting.Proxy_Set)


def download_image(url, to):
    return e926.down_from_url_bar(url, to, Sess, proxy=ProxySetting.Proxy_Set)


async def async_get(url):
    Client, key = await AsyncClients.alloc_client()
    data = await Client.get(url)
    AsyncClients.free_client(Client, key)
    return data


async def async_download_image(url, to):
    Client, key = await AsyncClients.alloc_client()
    resp = await pixivic.download_image_async_bar(to, url, Client)
    AsyncClients.free_client(Client, key)
    return resp


def get_query_page_data(keys, page, type='illust_and_ugoira', mode='safe', blt=200, bgt=20000, start_date=None, end_date=None):
    if type not in ['illust', 'all']:
        raise ValueError("not a good type")
    if mode not in ['all', 'r18', 'safe']:
        raise ValueError("strange mode")
    url = make_query_url(keys=keys, page=page, type=type, mode=mode, blt=blt, bgt=bgt,
                         start_date=start_date, end_date=end_date)
    rep = sync_get(url)
    if rep.status_code != 200:
        raise ValueError("not a good code " + str(rep))
    dat = rep.json()
    return dat['body']['illustManga']


async def get_query_page_data_async(keys, page, pack, type='illust_and_ugoira', mode='safe'):
    if type not in ['illust', 'all', 'illust_and_ugoira']:
        raise ValueError("not a good type")
    if mode not in ['all', 'r18', 'safe']:
        raise ValueError("strange mode")
    url = make_query_url(keys=keys, page=page, type=type, mode=mode, blt=pack['blt'], bgt=pack['bgt'],
                         start_date=pack['start_date'], end_date=pack['end_date'], s_mode=pack['s_mode'])
    rep = await async_get(url)
    if rep.status_code != 200:
        raise ValueError("not a good code " + str(rep))
    dat = rep.json()
    return dat['body']['illustManga']


def get_query_image_data(id):
    url = make_image_url(id)
    rep = sync_get(url)
    if rep.status_code != 200:
        raise ValueError("not a good code " + str(rep))
    dat = rep.json()
    data = dat['body']
    return data


def search_normalize(search0):
    return ' '.join(search0.split())


def normal_get_page(search, pack, page, mode):
    search0 = search + '$' + mode
    dat = pixivBuffer.has_search_buffer(search0, page)
    if dat:
        return dat
    data = get_query_page_data(pack['last'], page, blt=pack['blt'], bgt=pack['bgt'], mode=mode,
                               start_date=pack['start_date'], end_date=pack['end_date'])
    pixivBuffer.save_search_buffer(search0, page, data)
    return data


async def normal_get_page_async(search, pack, page, mode):
    search0 = search + '$' + mode
    dat = pixivBuffer.has_search_buffer(search0, page)
    if dat:
        return dat
    data = await get_query_page_data_async(pack['last'], page, pack=pack, mode=mode)
    pixivBuffer.save_search_buffer(search0, page, data)
    return data


def get_illustid(event, search, mode):  # ret [true?false?], data
    result, pack = pixivParser.pixiv_parser(search)
    if result == pixivParser.PPARSER_ERROR:
        return False, pack
    try:
        if result == pixivParser.PPARSER_NORMAL:
            pack['last'] = pack['last'].strip()
            if pack['last'] == '':
                pack['last'] = '伊布家族'
            data1 = normal_get_page(search, pack, 1, mode)
            Cnt = data1['total']
            print(' total %d ' % Cnt, end='')
            pages = Cnt//60
            if pages == 0:
                pages = 1
            else:
                if Cnt%60 > 10:
                    pages += 1
            if Cnt == 0:
                return False, "没找到满足条件作品"
            rnd = random.randint(1, pages)
            print(' div into %d pages and choose %d ' % (pages, rnd))
            datas = normal_get_page(search, pack, rnd, mode)
            illusts = datas['data']
            # illusts = pixivBuffer.filter_over_pages(illusts, pack['max_page'])
            if len(illusts) == 0:
                return False, "目前没找到满足条件作品"
            bond = pixivBuffer.bondage_with_seen(illusts, event)
            random.shuffle(bond)
            bond = sorted(bond, key=lambda i:i[0])
            return True, [Cnt, bond[0][1], pack['max_page']]
        else:
            return False, "目前还不支持~"
    except ValueError:
        return False, "出了点问题"


def download_illust(id, maxpg=3):
    if pixivBuffer.IllustBuffer.has(id):
        idata = pixivBuffer.IllustBuffer.get(id)
    else:
        idata = get_query_image_data(id)
        pixivBuffer.IllustBuffer.add(id, idata)
    print('得到' + str(id) + '数据完成')
    ret = []
    imgn = 0
    for img in idata:
        if imgn >= maxpg:
            break
        url = img['urls']['regular']
        fname = os.path.split(url)[-1]
        to = 'imgs/pixiv/' + fname
        if not os.path.isfile(to):
            if not download_image(url, to):
                return None
            img = cv2.imread(to)
            cv2.imwrite(to, img)
        ret.append(mirai.models.message.Image(path=to))
        imgn += 1
    if imgn != len(idata):
        ret.append("\n还有 %d 图片"%(len(idata) - imgn))
    return ret


async def download_illust_async(id, maxpg=10):
    if pixivBuffer.IllustBuffer.has(id):
        idata = pixivBuffer.IllustBuffer.get(id)
    else:
        try:
            idata = get_query_image_data(id)
        except:
            return None
        pixivBuffer.IllustBuffer.add(id, idata)
    print('得到' + str(id) + '数据完成')
    ret = []
    imgn = 0
    for img in idata:
        if imgn >= maxpg:
            break
        ratio = max(img['height']*1.0/img['width'], 1/(img['height']*1.0/img['width']))
        if ratio >= RATIO_THRESHOLD:
            url = img['urls']['original']
        else:
            url = img['urls']['regular']
        fname = os.path.split(url)[-1]
        to = 'imgs/pixiv/' + fname
        if not os.path.isfile(to):
            if not await async_download_image(url, to):
                return None
            img = cv2.imread(to)
            cv2.imwrite(to, img)
        ret.append(mirai.models.message.Image(path=to))
        imgn += 1
    if imgn != len(idata):
        ret.append("\n[还有 %d 图片]" % (len(idata) - imgn))
    return ret


async def download_illust_async_ex(id, maxpg=10, origin=False):
    if pixivBuffer.IllustBuffer.has(id):
        idata = pixivBuffer.IllustBuffer.get(id)
    else:
        try:
            idata = get_query_image_data(id)
        except:
            return None
        pixivBuffer.IllustBuffer.add(id, idata)
    print('得到' + str(id) + '数据完成')
    ret = []
    imgn = 0
    tasks = []
    for img in idata:
        if imgn >= maxpg:
            break
        ratio = max(img['height']*1.0/img['width'], 1/(img['height']*1.0/img['width']))
        if origin or ratio >= RATIO_THRESHOLD:
            url = img['urls']['original']
        else:
            url = img['urls']['regular']
        fname = os.path.split(url)[-1]
        to = 'imgs/pixiv/' + fname

        async def single_download(url0, to_dir):
            if not os.path.isfile(to_dir):
                if not await async_download_image(url0, to_dir):
                    return None
                img = cv2.imread(to_dir)
                cv2.imwrite(to_dir, img)
            return to_dir
        tasks.append(single_download(url, to))
        imgn += 1

    result = await asyncio.gather(*tasks)
    for id in result:
        if not id:
            return None
        ret.append(mirai.models.message.Image(path=id))
    if imgn != len(idata):
        ret.append("\n[还有 %d 图片]" % (len(idata) - imgn))
    return ret


def make_illust_info_page(id):
    return 'https://www.pixiv.net/ajax/illust/%s?lang=zh' % (str(id))


async def get_illust_info_async(id):
    url = make_illust_info_page(id)
    try:
        resp = await async_get(url)
        return resp.json()['body']
    except:
        return None


def is_info_r18_1(info):
    return info['sl'] > 4


def is_info_r18_2(info):
    r18s = ['R-18', 'R18', 'R18G', 'r-18', 'r18', 'r18g', 'R-18G', 'r-18g']
    if type(info['tags']) is dict:
        for a in info['tags']['tags']:
            if a['tag'] in r18s:
                return True
    else:
        for a in info['tags']:
            if a in r18s:
                return True
    return False


# todo
# api: https://www.pixiv.net/ajax/search/artworks/%E3%82%A4%E3%83%BC%E3%83%96%E3%82%A4?
# word=%E3%82%A4%E3%83%BC%E3%83%96%E3%82%A4&order=date_d&mode=all&p=1&s_mode=s_tag&type=all&lang=zh
# eevee


# https://www.pixiv.net/ajax/search/artworks/%E3%82%A4%E3%83%BC%E3%83%96%E3%82%A4%20%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3?
# word=%E3%82%A4%E3%83%BC%E3%83%96%E3%82%A4%20%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3&order=date_d
# &mode=all&p=1&s_mode=s_tag&type=all&lang=zh
# eevee pokemon


# https://www.pixiv.net/ajax/search/artworks/%E3%82%A4%E3%83%BC%E3%83%96%E3%82%A4%20%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3?
# word=%E3%82%A4%E3%83%BC%E3%83%96%E3%82%A4%20%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3&
# order=date_d&mode=all
# &blt=200&bgt=19999&
# p=1&s_mode=s_tag&type=all&lang=zh

# search:
# a -na -nb (oa OR ob OR oc OR od)


def make_search_user(search_name):
    return 'https://www.pixiv.net/search_user.php?nick=%s&s_mode=s_usr' % (urllib.parse.quote(search_name))


async def search_user_async(s_name):
    print('now search ' + s_name, end='')
    url = make_search_user(s_name)
    print('url: ' + url)
    try:
        res = await async_get(url)
        if res.status_code != 200:
            raise ValueError("not a good code" + str(res.status_code))
        sp = BeautifulSoup(res.content, 'html.parser')
        users = sp.find('ul', class_='user-recommendation-items').find_all('li', class_='user-recommendation-item')
        ret = []
        for user in users:
            h_url = user.a['data-src']
            uid = user.a['href'].split('/')[-1]
            name = user.h1.text
            descript = user.p.text
            show_illusts = user.find('ul', class_='images').find_all('li', class_='action-open-thumbnail')
            show_ill = []
            for a in show_illusts:
                try:
                    show_ill.append(a['data-src'])
                except KeyError:
                    continue
            ret.append({
                'header': h_url,
                'id': uid,
                'name': name,
                'description': descript,
                'show_illusts': show_ill
            })
        return ret
    except ValueError:
        return None
    except AttributeError:
        return '没找到~'


async def download_user_header_async(user, to_scale=64):
    url = user['header']
    id = user['id']
    fname = os.path.join('pixiv', 'headers')
    os.makedirs(fname) if not os.path.exists(fname) else None
    fname = os.path.join(fname, user['id'] + '.' + url.split('.')[-1])
    result = await async_download_image(url, fname)
    if not result:
        return None
    if url.split('.')[-1] not in ['png', 'jpeg', 'jpg']:
        return fname
    img = cv2.imread(fname)
    img = cv2.resize(img, (to_scale, to_scale), interpolation=cv2.INTER_AREA)
    cv2.imwrite(fname, img)
    return fname


def make_user_illusts_enum_url(uid): # ~['body']['illusts'].keys()
    return 'https://www.pixiv.net/ajax/user/%s/profile/all?lang=zh' % str(uid)


def make_user_illusts_search_url(uid, tag, offset):
    return 'https://www.pixiv.net/ajax/user/%s/illusts/tag?tag=%s&offset=%d&limit=48&lang=zh' % (str(uid), urllib.parse.quote(tag), offset)


def is_illust(idata):
    return idata['illustType'] == 0


MAX_ATTEMPS = 5


async def random_get_user_illust(uid, qid, mode='safe'):
    eurl = make_user_illusts_enum_url(uid)
    try:
        resp = await async_get(eurl)
        imgs = list(resp.json()['body']['illusts'].keys())
        random.shuffle(imgs)
        iimg = []
        for i in imgs:
            iimg.append((pixivBuffer.VisData.seen_count(qid, i), i))
        iimg = sorted(iimg, key=lambda i: i[0])
        attemp = 0
        for _, id in iimg:
            if attemp > MAX_ATTEMPS:
                return None
            if pixivBuffer.have_intro_buffer(id):
                intro = pixivBuffer.get_intro_buffer(id)
            else:
                attemp += 1
                print('attemp ' + str(attemp))
                intro = await get_illust_info_async(id)
                if not intro:
                    return None
                pixivBuffer.save_intro_buffer(id, intro)
            if not is_illust(intro):
                continue
            if mode == 'safe':
                if is_info_r18_1(intro) or is_info_r18_2(intro):
                    continue
            return intro, len(iimg)
        return None
    except ValueError:
        return None


async def tag_get_user_illust(uid, qid, tag, mode='safe'):
    eurl = make_user_illusts_search_url(uid, tag, 0)
    try:
        resp = await async_get(eurl)
        if resp.status_code != 200:
            raise ValueError("not a good code " + str(resp.status_code))
        resp = resp.json()
        bond = []
        total = resp['body']['total']
        if total <= 48:
            works = resp['body']['works']
        else:
            offmax = total - 48
            offrand = random.randint(0, offmax)
            resp = await async_get(make_user_illusts_search_url(uid, tag, offrand))
            resp = resp.json()
            works = resp['body']['works']
        random.shuffle(works)
        for i in works:
            bond.append((pixivBuffer.VisData.seen_count(qid, i['id']), i))
        bond = sorted(bond, key=lambda a: a[0])
        if mode == 'all':
            return bond[0][1], total
        for _,i in bond:
            if mode == 'safe':
                if is_info_r18_1(i) or is_info_r18_2(i):
                    continue
                return i, total
            if mode == 'r18':
                if is_info_r18_2(i):
                    return i, total
        return None
    except ValueError:
        return None


async def get_illustid_async(event, search, mode):  # ret [true?false?], data
    result, pack = pixivParser.pixiv_parser(search)
    if result == pixivParser.PPARSER_ERROR:
        return False, "Parser Error:  " + pack
    if result == pixivParser.PPARSER_NORMAL:
        pack['last'] = pack['last'].strip()
        if pack['last'] == '':
            pack['last'] = DEFAULT_SEARCH
        data1 = await normal_get_page_async(search, pack, 1, mode)
        Cnt = data1['total']
        print(' total %d ' % Cnt, end='')
        pages = Cnt//60
        if pages == 0:
            pages = 1
        else:
            if Cnt % 60 > 10:
                pages += 1
        if Cnt == 0:
            return False, "没找到满足条件作品"
        rnd = random.randint(1, pages)
        print(' div into %d pages and choose %d ' % (pages, rnd))
        datas = await normal_get_page_async(search, pack, rnd, mode)
        illusts = datas['data']
        # illusts = pixivBuffer.filter_over_pages(illusts, pack['max_page'])
        if len(illusts) == 0:
            return False, "目前没找到满足条件作品"
        bond = pixivBuffer.bondage_with_seen(illusts, event)
        random.shuffle(bond)
        bond = sorted(bond, key=lambda i: i[0])
        return True, [Cnt, bond[0][1], pack['max_page'], pack['origin']]
    elif result == pixivParser.PPARSER_OF_ID:
        id = pack['id']
        if pixivBuffer.have_intro_buffer(id):
            info = pixivBuffer.get_intro_buffer(id)
        else:
            info = await get_illust_info_async(id)
            if not info:
                return False, '查找作品信息出了点问题pwp'
            pixivBuffer.save_intro_buffer(id, info)
        r1 = is_info_r18_1(info)
        r2 = is_info_r18_2(info)
        if r1 != r2:
            print(str(id) + '  r18不确定')
        if (r1 or r2) and (mode == 'safe'):
            return False, "不可以涩涩的嘛"
        return True, [1, info, pack['max_page'], pack['origin']]
    elif result == pixivParser.PPARSER_OF_AUTHOR:
        au = pack['author']
        tag = pack['last'].strip()
        if tag == '':
            if mode == 'r18':
                result = await tag_get_user_illust(au, pixivBuffer.get_event_id(event), 'R-18', 'all')
                if not result:
                    return False, '查找失败或是没找到qwq'
                return True, [result[1], result[0], pack['max_page'], pack['origin']]
            result = await random_get_user_illust(au, pixivBuffer.get_event_id(event), mode)
            if not result:
                return False, '查找失败或是没找到qwq'
            return True, [result[1], result[0], pack['max_page'], pack['origin']]
        else:
            tags = tag.split()
            if len(tags) > 1:
                return False, "搜索作者只能最多指定1个tag"
            result = await tag_get_user_illust(au, pixivBuffer.get_event_id(event), tag, mode)
            if not result:
                return False, '查找失败或是没找到qwq'
            return True, [result[1], result[0], pack['max_page'], pack['origin']]
    else:
        return False, "目前还不支持"


def make_user_query_url(uid):
    return 'https://www.pixiv.net/ajax/user/%s?full=1&lang=zh' % str(uid)


def trans_localtime(tstr):
    utc = datetime.datetime.fromisoformat(tstr)
    # utc = pytz.timezone('UTC').localize(date)
    cnn = utc.astimezone(pytz.timezone('Asia/Shanghai'))
    return str(cnn)[:-6]


if __name__ == '__main__':
    url0 = 'https://www.pixiv.net/search_user.php?nick=Anom&s_mode=s_usr'
    resp = sync_get(url0)
    pass


async def stalk_illusts_in_time(keyword, s_time, e_time, f_mark=20, mode='safe'):
    pack = {
        'bgt': 9999999,
        'blt': f_mark,
        'max_page': 200,
        'last': keyword,
        'start_date': s_time,
        'end_date': e_time,
        's_mode': 's_tag',
        'origin': True
    }
    enums = []
    search = str(pack)
    data1 = await normal_get_page_async(search, pack, 1, mode)
    Cnt = data1['total']
    enums.extend(data1['data'])
    pages = (Cnt // 60) + (1 if Cnt % 60 else 0)
    for pg in range(2, pages+1):
        datan = await normal_get_page_async(search, pack, pg, mode)
        enums.extend(datan['data'])
    return enums


async def stalk_download_illusts(id, to_dir):
    idata = get_query_image_data(id)
    ret = []
    tasks = []
    for img in idata:
        url = img['urls']['original']
        fname = os.path.split(url)[-1]
        to = to_dir + fname

        async def single_download(url0, to_dir):
            if not os.path.isfile(to_dir):
                if not await async_download_image(url0, to_dir):
                    return None
            return to_dir
        tasks.append(single_download(url, to))
    result = await asyncio.gather(*tasks)
