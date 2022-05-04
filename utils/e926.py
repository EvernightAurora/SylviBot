import requests
import urllib
from bs4 import BeautifulSoup
import os
from tqdm import tqdm
import httpx
from utils import pixivic
from utils import ClientControl
from utils import configLoader


norm_search0 = r'~eevee ~vaporeon ~jolteon ~flareon ~espeon ~umbreon ~leafeon ~glaceon ' \
              r'~sylveon order:random'
norm_search_r0 = r'~eevee ~vaporeon ~jolteon ~flareon ~espeon ~umbreon ~leafeon ~glaceon ' \
              r'~sylveon order:random -gore -anthro -human'
score_threshold0 = 50
score_threshold_r0 = 100
favcount_threshold0 = 150
favcount_threshold_r0 = 350

norm_search = ''
norm_search_r = ''
score_threshold = ''
score_threshold_r = ''
favcount_threshold = ''
favcount_threshold_r = ''
USE_FAV = True

inited = False


def on_init():
    global inited, norm_search0, norm_search_r0, score_threshold_r0, score_threshold0
    global favcount_threshold0, favcount_threshold_r0
    global norm_search, norm_search_r, score_threshold_r, score_threshold, favcount_threshold, favcount_threshold_r
    if inited:
        return
    inited = True
    norm_search0 = configLoader.get_config('926_default_search', norm_search0)
    score_threshold0 = configLoader.get_config('926_score_threshold', score_threshold0)
    favcount_threshold0 = configLoader.get_config('926_favcount_threshold', favcount_threshold0)

    norm_search_r0 = configLoader.get_config('621_default_search', norm_search0)
    score_threshold_r0 = configLoader.get_config('621_score_threshold', score_threshold0)
    favcount_threshold_r0 = configLoader.get_config('621_favcount_threshold', favcount_threshold0)

    norm_search = norm_search0
    norm_search_r = norm_search_r0
    score_threshold = score_threshold0
    score_threshold_r = score_threshold_r0
    favcount_threshold = favcount_threshold0
    favcount_threshold_r = favcount_threshold_r0


url0 = r'https://e926.net/posts?tags='
url1 = r'https://e621.net/posts?tags='

ex_search = r' -type:mp4 -type:swf -type:zip -type:webm'
ex_nogif_search = r' -animated'
ex_gif_limit = r' filesize:..5MB'

allowed_ext = ['png', 'jpg', 'gif']

Sess = requests.session()
Sess.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/96.0.4664.110 Safari/537.36'}
Sess.trust_env = False

AsyncClients = ClientControl.AsyncClientControl(4)


def search_filter(cds):
    return [ci for ci in cds if (ci['data-file-ext'] in allowed_ext)]


def pre_search_set(keys, ero=False):
    if USE_FAV:
        if ('favcount:' not in keys) and ('id:' not in keys):
            keys += ' favcount:>=' + str(favcount_threshold if not ero else favcount_threshold_r)
    else:
        if ('score:' not in keys) and ('id:' not in keys):
            keys += ' score:>=' + str(score_threshold if not ero else score_threshold_r)
    if 'order:' not in keys:
        keys += ' order:random '
    if ('gif' not in keys and 'animated' not in keys) and 'id:' not in keys:
        keys += ex_nogif_search
    elif('-gif' not in keys and '-type:gif' not in keys and '-animated' not in keys) and 'filesize:' not in keys and 'id:' not in keys:
        keys += ex_gif_limit
    return keys + ex_search


def search_core(url):
    global Sess
    res = Sess.get(url)
    if res.status_code != 200:
        raise Exception("Net error")
    nb = BeautifulSoup(res.content, 'html.parser')
    ctn = nb.find(id='posts-container')
    childs = ctn.find_all('article')
    fc = search_filter(childs)
    return [{
        'id': i['data-id'],
        'l_source': i['data-large-file-url'],
        'source': i['data-file-url'],
        'rating': i['data-rating'],
        'score': int(i['data-score']),
        'fav': int(i['data-fav-count']),
        'type': i['data-file-ext']
    } for i in fc]


async def search_core_async(url):
    print(os.path.split(url)[-1])
    global Sess
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, cookies=Sess.cookies)
        if resp.status_code != 200:
            raise Exception("Net Error")
    nb = BeautifulSoup(resp.content, 'html.parser')
    ctn = nb.find(id='posts-container')
    childs = ctn.find_all('article')
    fc = search_filter(childs)
    return [{
        'id': i['data-id'],
        'l_source': i['data-large-file-url'],
        'source': i['data-file-url'],
        'rating': i['data-rating'],
        'score': int(i['data-score']),
        'fav': int(i['data-fav-count']),
        'type': i['data-file-ext']
    } for i in fc]


def get_searchs(keys=''):
    if not keys:
        global norm_search
        keys = norm_search
    keys = pre_search_set(keys, ero=False)
    url = url0 + urllib.parse.quote(keys)
    print(url)
    return search_core(url)


def get_searchs_r(keys=''):
    if not keys:
        global norm_search_r
        keys = norm_search_r
    keys = pre_search_set(keys, ero=True)
    url = url1 + urllib.parse.quote(keys)
    print(url)
    return search_core(url)


async def get_searchs_async(keys=''):
    if not keys:
        global norm_search
        keys = norm_search
    keys = pre_search_set(keys, ero=False)
    url = url0 + urllib.parse.quote(keys)
    return await search_core_async(url)


async def get_searchs_r_async(keys=''):
    if not keys:
        global norm_search_r
        keys = norm_search_r
    keys = pre_search_set(keys, ero=True)
    url = url1 + urllib.parse.quote(keys)
    return await search_core_async(url)


def down_from_url_bar(url, dst, sess=Sess, proxy=None):
    try:
        response = sess.get(url, stream=True, proxies=proxy)  # (1)
        if 'content-length' in response.headers:
            file_size = int(response.headers['content-length'])  # (2)
        else:
            file_size = 0
        if os.path.exists(dst):
            first_byte = os.path.getsize(dst)  # (3)
        else:
            first_byte = 0
        # if first_byte >= file_size:  # (4)
        #     return file_size

        # header = {"Range": f"bytes={first_byte}-{file_size}"}
        header = None

        pbar = tqdm(total=file_size, initial=first_byte, unit='B', unit_scale=True, desc=dst)
        req = sess.get(url, headers=header, stream=True, proxies=proxy)  # (5)
        with open(dst, 'ab') as f:
            for chunk in req.iter_content(chunk_size=4096):  # (6)
                if chunk:
                    f.write(chunk)
                    pbar.update(4096)
        pbar.close()
        return file_size + 1
    except:
        return None


def download_image(imgf):
    savepath = 'imgs/e926'
    os.makedirs(savepath) if not os.path.exists(savepath) else None
    sn = os.path.join(savepath, imgf['id'] + '.' + imgf['type'])
    if os.path.isfile(sn):
        return sn
    global Sess
    down_from_url_bar(imgf['l_source'], sn)
    '''
    imgs = Sess.get(imgf['l_source'])
    with open(sn, 'wb') as f:
        f.write(imgs.content)
    '''
    return sn


def download_image_r(imgf):
    savepath = 'imgs/e621'
    os.makedirs(savepath) if not os.path.exists(savepath) else None
    sn = os.path.join(savepath, imgf['id'] + '.' + imgf['type'])
    if os.path.isfile(sn):
        return sn
    global Sess
    down_from_url_bar(imgf['l_source'], sn)
    '''
    imgs = Sess.get(imgf['l_source'])
    with open(sn, 'wb') as f:
        f.write(imgs.content)
    '''
    return sn


async def download_image_r_async(imgf):
    savepath = 'imgs/e621'
    os.makedirs(savepath) if not os.path.exists(savepath) else None
    sn = os.path.join(savepath, imgf['id'] + '.' + imgf['type'])
    if os.path.isfile(sn):
        return sn
    url = imgf['source']
    client, tkey = await AsyncClients.alloc_client()
    if not await pixivic.download_image_async_bar(sn, url, client0=client):
        raise Exception("download error")
    '''
    global Sess
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, cookies=Sess.cookies)
            with open(sn, 'wb') as f:
                f.write(resp.content)
        except:
            return None
    '''
    AsyncClients.free_client(client, tkey)
    return sn


if __name__ == '__main__':
    bs = get_searchs_r()
    print(download_image_r(bs[0]))
    pass
