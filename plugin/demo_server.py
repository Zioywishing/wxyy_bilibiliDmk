#!/usr/env python3
# -*- coding: UTF-8 -*-

from flask import Flask, request, send_file, make_response
from flask_cors import CORS
import json
import random

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://yiyan.baidu.com"}})

wordbook = []

def make_json_response(data, status_code=200):
    response = make_response(json.dumps(data), status_code)
    response.headers["Content-Type"] = "application/json"
    return response

@app.route("/logo.png")
async def plugin_logo():
    """
        注册用的：返回插件的logo，要求48 x 48大小的png文件.
        注意：API路由是固定的，事先约定的。
    """
    return send_file('logo.png', mimetype='image/png')


@app.route("/.well-known/ai-plugin.json")
async def plugin_manifest():
    """
        注册用的：返回插件的描述文件，描述了插件是什么等信息。
        注意：API路由是固定的，事先约定的。
    """
    host = request.host_url
    with open(".well-known/ai-plugin.json", encoding="utf-8") as f:
        text = f.read().replace("PLUGIN_HOST", host)
        return text, 200, {"Content-Type": "application/json"}


@app.route("/.well-known/openapi.yaml")
async def openapi_spec():
    """
        注册用的：返回插件所依赖的插件服务的API接口描述，参照openapi规范编写。
        注意：API路由是固定的，事先约定的。
    """
    with open(".well-known/openapi.yaml", encoding="utf-8") as f:
        text = f.read()
        return text, 200, {"Content-Type": "text/yaml"}
    
import os
comment_path = 'bilibili1.csv'
if os.path.exists(comment_path):
    os.remove(comment_path)

@app.route('/test',methods=['POST'])
async def test():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.data)
    bilibili_url=request.json.get('url', "")
    bv_id=bilibili_url
    cid=get_cid(bv_id)
    spider(cid)
    return make_json_response({"message":"成功传入","url_message":bilibili_url})

import requests
import re
def spider(cid):
    url = f'https://comment.bilibili.com/{cid}.xml'
    headers = {
        'cookie':"b_lsid=310E7616E_18B7F8BB2C1; _uuid=FBBEDF84-10534-3F4F-CABE-947D7E449510443649infoc; buvid_fp=d82facd6e828f7a0377c00231aa7a3ac; buvid3=9A8D7049-2E3A-1FB4-35F3-E9767149864443888infoc; b_nut=1698651945; buvid4=EE2224ED-C2F7-001B-1982-727B92ACA31843888-023103015-%2FKPDqUY3StH6LeVcWJARtw%3D%3D; enable_web_push=DISABLE; header_theme_version=CLOSE; CURRENT_FNVAL=4048; rpdid=|(JlklRl)~lm0J'uYm)Ylumm); bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTg5MTEyMDAsImlhdCI6MTY5ODY1MTk0MCwicGx0IjotMX0.i-sWHDSCqyeWz2D3RtR20FEI0NnqrjcoBw2Ix1qnLBA; bili_ticket_expires=1698911140; home_feed_column=5; browser_resolution=1872-923; sid=8m6ozd93",
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0'
    }
    resq = requests.get(url, headers=headers)
    resq.encoding = resq.apparent_encoding
    content_list = re.findall('<d p=".*?">(.*?)</d>', resq.text)
    # print(content_list)
    for item in content_list:
        with open(comment_path, 'a', encoding='utf-8') as fin:
            fin.write(item + '\n')
        # print(item)
    # print("down")

def get_cid(BV):
    print("BV是："+BV)
    cidurl = f'https://api.bilibili.com/x/player/pagelist?bvid={BV}&jsonp=jsonp'
    headers = {
        'cookie':"b_lsid=310E7616E_18B7F8BB2C1; _uuid=FBBEDF84-10534-3F4F-CABE-947D7E449510443649infoc; buvid_fp=d82facd6e828f7a0377c00231aa7a3ac; buvid3=9A8D7049-2E3A-1FB4-35F3-E9767149864443888infoc; b_nut=1698651945; buvid4=EE2224ED-C2F7-001B-1982-727B92ACA31843888-023103015-%2FKPDqUY3StH6LeVcWJARtw%3D%3D; enable_web_push=DISABLE; header_theme_version=CLOSE; CURRENT_FNVAL=4048; sid=nvzw4wae; rpdid=|(JlklRl)~lm0J'uYm)Ylumm); bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTg5MTEyMDAsImlhdCI6MTY5ODY1MTk0MCwicGx0IjotMX0.i-sWHDSCqyeWz2D3RtR20FEI0NnqrjcoBw2Ix1qnLBA; bili_ticket_expires=1698911140; home_feed_column=5; browser_resolution=1872-923",
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0'
    }
    cidres = requests.get(cidurl, headers=headers)
    print(cidres.json())
    cid = cidres.json()['data'][0]['cid']
    # print(cid)
    return cid

@app.route('/')
def index():
    return 'welcome to my webpage!'

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8081)