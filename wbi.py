from functools import reduce
from hashlib import md5
import urllib.parse
import time
import requests
import os
import base64
import random

os.environ['NO_PROXY'] = 'https://api.bilibili.com'
req_headers = dict()
req_headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0'
# req_headers['Referer'] = 'https://www.bilibili.com'
req_headers['Accept-Encoding'] = 'utf-8'
req_headers['Accept-Language'] = 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en;q=0.3,en-US;q=0.2'
req_headers['Accept'] = 'application/json'
req_headers['Cache-Control'] = 'no-cache'
req_headers['Connection'] = 'keep-alive'
# req_headers['Origin'] = 'https://www.bilibili.com'
req_headers['Pragma'] = 'no-cache'

mixinKeyEncTab = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52
]

websiteTagNames = [
  "span", "div", "p", "a", "img", "input", "button", "ul", "ol", "li",
  "h1", "h2", "h3", "h4", "h5", "h6", "form", "textarea", "select", "option",
  "table", "tr", "td", "th", "label", "strong", "em", "section", "article",
]

session = requests.session()
cookies = session.get("https://bilibili.com", headers=req_headers).cookies
# b_3 = requests.get("https://api.bilibili.com/x/frontend/finger/spi", headers=req_headers).json()['data']['b_3']
# cookies = {
#     'buvid3': b_3,
#     'buvid4': b_4
# }
# cookies = {'Cookies': 'buvid3='+b_3}
# cookies.set("buvid3", b_3)
# print(cookies)


def get_mixin_key(orig: str):
    '对 imgKey 和 subKey 进行字符顺序打乱编码'
    return reduce(lambda s, i: s + orig[i], mixinKeyEncTab, '')[:32]


def enc_wbi(params: dict, img_key: str, sub_key: str):
    '为请求参数进行 wbi 签名'
    mixin_key = get_mixin_key(img_key + sub_key)
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


def get_wbi_keys():
    resp = requests.get('https://api.bilibili.com/x/web-interface/nav', headers=req_headers, cookies=cookies)
    resp.raise_for_status()
    json_content = resp.json()
    img_url: str = json_content['data']['wbi_img']['img_url']
    sub_url: str = json_content['data']['wbi_img']['sub_url']
    img_key = img_url.rsplit('/', 1)[1].split('.')[0]
    sub_key = sub_url.rsplit('/', 1)[1].split('.')[0]
    return img_key, sub_key


def get_access_spi():
    resp = requests.get("https://api.bilibili.com/x/frontend/finger/spi", headers=req_headers)
    json_content = resp.json()['data']
    return json_content['b_3'], json_content['b_4'], int(time.time())


def get_wts_w_rid(params):
    img_key, sub_key = get_wbi_keys()
    signed_params = enc_wbi(
        params=params,
        sub_key=sub_key,
        img_key=img_key,
    )
    query = urllib.parse.urlencode(signed_params)
    # print(signed_params)
    print(query)
    return signed_params


def get_acc_info(mid: int):
    req_url = 'https://api.bilibili.com/x/space/wbi/acc/info'
    req_params = dict()
    req_params['mid'] = mid
    req_params['token'] = ''
    req_params['platform'] = 'web'
    req_params['web_location'] = 1550101
    signed_params = get_wts_w_rid(req_params)
    print(urllib.parse.urlencode(signed_params))
    response = requests.get(url=req_url, params=signed_params, headers=req_headers)
    return response


def get_search_acc(mid: int):
    req_url = 'https://api.bilibili.com/x/space/wbi/arc/search'
    req_params = dict()
    req_params['mid'] = mid
    req_params['pn'] = 1
    req_params['ps'] = 25
    req_params['index'] = 1
    req_params['order'] = 'pubdate'
    req_params['order_avoided'] = 'true'
    req_params['platform'] = 'web'
    req_params['web_location'] = 1550101
    req_params['dm_img_list'] = '[]'
    req_params['dm_img_str'] = base64.b64encode(bytes(random.choices(range(0x20, 0x7f), k=random.randint(16, 64))))[:-2].decode()
    req_params['dm_cover_img_str'] = base64.b64encode(bytes(random.choices(range(0x20, 0x7f), k=random.randint(32, 128))))[:-2].decode()
    req_params['dm_img_inter'] = '{"ds":[],"wh":[0,0,0],"of":[0,0,0]}'
    # req_params['dm_rand'] = 'ABCDEFGHIJK'
    # req_params['dm_img_list'] = '[]'
    # req_params['dm_img_str'] = ''.join(random.sample('ABCDEFGHIJK', 2))
    # req_params['dm_cover_img_str'] = ''.join(random.sample('ABCDEFGHIJK', 2))
    # req_params['dm_img_inter'] = '{"ds":[{"t":2,"c":"Y2xlYXJmaXggZy1zZWFyY2ggc2VhcmNoLWNvbnRhaW5lcg","p":[1668,72,676],"s":[140,602,696]},{"t":2,"c":"c2VjdGlvbiB2aWRlbyBsb2FkaW5nIGZ1bGwtcm93cw","p":[749,9,1348],"s":[358,3100,2232]}],"wh":[339,113,113],"of":[246,492,246]}'
    signed_params = get_wts_w_rid(req_params)
    response = requests.get(url=req_url, params=signed_params, headers=req_headers, cookies=cookies)
    return response


def get_user_cards(uids: str):
    reqUrl = 'https://api.vc.bilibili.com/account/v1/user/cards'
    req_params = dict()
    req_params['uids'] = uids
    # req_params['token'] = ''
    req_params['platform'] = 'web'
    req_params['web_location'] = 1550101
    signed_params = get_wts_w_rid(req_params)
    response = requests.get(url=reqUrl, params=signed_params, headers=req_headers)
    print(response)
    return response


def get_status_info_by_uids(uids_list: list):
    req_headers['Content-type'] = 'application/json'  #'application/x-www-form-urlencoded'
    reqUrl = 'https://api.live.bilibili.com/room/v1/Room/get_status_info_by_uids'
    req_params = {
        "uids[]": uids_list,
    }
    response = requests.get(url=reqUrl, params=req_params, headers=req_headers)
    return response

