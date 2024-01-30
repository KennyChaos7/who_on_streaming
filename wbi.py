from functools import reduce
from hashlib import md5
import urllib.parse
import time
import requests
import os

from typing import Tuple

os.environ['NO_PROXY'] = 'https://api.bilibili.com'
# reqHeaders = {
#     'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
#     'Content-Encoding': 'gzip',
#     'Accept': 'application/json',
#     'Accept-Language': 'zh-CN,zh;q=0.9',
#     'Connection': 'close'
# }
reqHeaders = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'referer': 'https://www.bilibili.com',
        'Accept-Encoding': 'utf-8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en;q=0.3,en-US;q=0.2',
        'Accept': 'application/json, text/plain, */*',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Origin': 'https://www.bilibili.com',
        'Pragma': 'no-cache'
    }

mixinKeyEncTab = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52
]

b_3 = requests.get("https://api.bilibili.com/x/frontend/finger/spi", headers=reqHeaders).json()['data']['b_3']
cookies = {
    'buvid3': b_3,
    # 'buvid4': b_4
}

def getMixinKey(orig: str):
    '对 imgKey 和 subKey 进行字符顺序打乱编码'
    return reduce(lambda s, i: s + orig[i], mixinKeyEncTab, '')[:32]


def encWbi(params: dict, img_key: str, sub_key: str):
    '为请求参数进行 wbi 签名'
    mixin_key = getMixinKey(img_key + sub_key)
    curr_time = round(time.time())
    params['wts'] = curr_time                                   # 添加 wts 字段
    params = dict(sorted(params.items()))                       # 按照 key 重排参数
    # 过滤 value 中的 "!'()*" 字符
    params = {
        k : ''.join(filter(lambda chr: chr not in "!'()*", str(v)))
        for k, v
        in params.items()
    }
    query = urllib.parse.urlencode(params)                      # 序列化参数
    wbi_sign = md5((query + mixin_key).encode()).hexdigest()    # 计算 w_rid
    params['w_rid'] = wbi_sign
    return params


def getWbiKeys():
    resp = requests.get('https://api.bilibili.com/x/web-interface/nav', headers=reqHeaders, cookies=cookies)
    resp.raise_for_status()
    json_content = resp.json()
    img_url: str = json_content['data']['wbi_img']['img_url']
    sub_url: str = json_content['data']['wbi_img']['sub_url']
    img_key = img_url.rsplit('/', 1)[1].split('.')[0]
    sub_key = sub_url.rsplit('/', 1)[1].split('.')[0]
    return img_key, sub_key

def get_access_spi():
    resp = requests.get("https://api.bilibili.com/x/frontend/finger/spi", headers=reqHeaders)
    json_content = resp.json()['data']
    return json_content['b_3'], json_content['b_4']


def get_wts_w_rid():
    img_key, sub_key = getWbiKeys()
    signed_params = encWbi(
        params={
            'foo': '114',
            'bar': '514',
            'baz': 1919810
        },
        img_key=img_key,
        sub_key=sub_key
    )
    query = urllib.parse.urlencode(signed_params)
    # print(signed_params)
    print(query)
    return signed_params['wts'], signed_params['w_rid']


def get_acc_info(mid: str):
    reqUrl = 'https://api.bilibili.com/x/space/wbi/acc/info'
    wts, w_rid = get_wts_w_rid()
    req_params = {
        "mid": mid,
        'w_rid': w_rid,
        'wts': wts
    }
    response = requests.get(url=reqUrl, params=req_params, headers=reqHeaders, cookies=cookies)
    print(response.json())
    return response


def get_user_cards(uids: str):
    reqUrl = 'https://api.vc.bilibili.com/account/v1/user/cards'
    wts, w_rid = get_wts_w_rid()
    req_params = {
        "uids": uids,
        'w_rid': w_rid,
        'wts': wts
    }
    response = requests.get(url=reqUrl, params=req_params, headers=reqHeaders)
    print(response)
    return response


def get_status_info_by_uids(uids_list: list):
    reqUrl = 'https://api.live.bilibili.com/room/v1/Room/get_status_info_by_uids'
    wts, w_rid = get_wts_w_rid()
    req_params = {
        "uids[]": uids_list,
        'w_rid': w_rid,
        'wts': wts
    }

    response = requests.get(url=reqUrl, params=req_params, headers=reqHeaders)
    print(response)
    return response



if __name__ == '__main__':
    get_wts_w_rid()
