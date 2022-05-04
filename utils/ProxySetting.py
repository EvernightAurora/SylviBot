import os
import yaml


with open('proxy_config.yaml', 'r') as f:
    configs = yaml.unsafe_load(f)


def get_config(name):
    global configs
    if name in configs.keys():
        return configs[name]
    else:
        return None


WIN_HTTPS_PROXY = get_config('win_proxy_https')
WIN_HTTP_PROXY = get_config('win_proxy_http')
GLOBAL_HTTPS_PROXY = get_config('proxy_https')
GLOBAL_HTTP_PROXY = get_config('proxy_http')


if os.getcwd()[0] in ['C', 'D', 'E', 'F', 'G']:   # windows
    HTTPS_PROXY = WIN_HTTPS_PROXY if WIN_HTTPS_PROXY else GLOBAL_HTTPS_PROXY
    HTTP_PROXY = WIN_HTTP_PROXY if WIN_HTTP_PROXY else GLOBAL_HTTP_PROXY
else:
    HTTPS_PROXY = GLOBAL_HTTPS_PROXY
    HTTP_PROXY = GLOBAL_HTTP_PROXY

Proxy_Set = {
    "https": HTTPS_PROXY,
    "http": HTTP_PROXY
}

Proxy_Set_For_HTTPX = {
    "https://": HTTPS_PROXY,
    "http://": HTTP_PROXY
}



