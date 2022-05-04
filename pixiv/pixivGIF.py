import zipfile
from pixiv import pixiv
import imageio
from utils import ImgDataStore
import os
from utils import ErrorSend


Ugoira_store: ImgDataStore.ImageData


def on_init():
    global Ugoira_store
    Ugoira_store = ImgDataStore.ImageData('pixiv/ugoira_meta.json')


def is_gif(idata):
    return idata['illustType'] == 2


def make_ugoira_meta_url(pid):
    return 'https://www.pixiv.net/ajax/illust/%s/ugoira_meta?lang=zh' % (str(pid))


async def adaptive_get_ugoira_meta(pid):
    global Ugoira_store
    pid = str(pid)
    if Ugoira_store.has(pid):
        return Ugoira_store.get(pid)
    url = make_ugoira_meta_url(pid)
    resp = await pixiv.async_get(url)
    dat = resp.json()
    Ugoira_store.add(pid, dat)
    return dat


def make_meta_save_to(url):
    file = os.path.split(url)[-1]
    return 'pixiv/ugoira/' + file


def unzip(fpath):
    fto = fpath[:-4]
    os.makedirs(fto) if not os.path.exists(fto) else None
    f = zipfile.ZipFile(fpath)
    fl = f.namelist()
    for fn in fl:
        f.extract(fn, fto)


def combine_gif(url, dat):
    filepath = 'pixiv/ugoira/' + os.path.split(url)[-1][:-4]
    '''
    def gcd(a, b):
        if b == 0:
            return a
        return gcd(b, a % b)

    delay0 = dat['body']['frames'][0]['delay']
    for p in dat['body']['frames']:
        delay0 = gcd(delay0, p['delay'])
    '''
    duras = []
    frames = []
    for p in dat['body']['frames']:
        fpath = os.path.join(filepath, p['file'])
        img = imageio.imread(fpath)
        frames.append(img)
        duras.append(0.001 * p['delay'])
    imageio.mimsave(filepath + '.gif', frames, 'GIF', duration=duras)
    return filepath + '.gif'


async def download_gif(pid, origin=False):
    dat = await adaptive_get_ugoira_meta(pid)
    if origin:
        url = dat['body']['originalSrc']
    else:
        url = dat['body']['src']
    filepath = 'pixiv/ugoira/' + os.path.split(url)[-1][:-4] + '.gif'
    if os.path.isfile(filepath):
        return filepath
    tpath = make_meta_save_to(url)
    if not os.path.isfile(tpath):
        rep = await pixiv.async_download_image(url, tpath)
        if not rep:
            return None
    unzip(fpath=tpath)
    print('unzip ' + os.path.split(tpath)[-1] + ' finish!!')
    ret = combine_gif(url, dat)
    return ret



