#!/usr/env python3
# -*- coding: UTF-8 -*-
import matplotlib as plt
import numpy as np
import jieba
from collections import Counter
from flask import Flask, request, send_file, make_response
from flask_cors import CORS
from getdm import Crawler_Bilibili_Danmu as cbd
import json
import random
import requests
import re
import sqlite3
import os
from random import randint

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://yiyan.baidu.com"}})

db_path = './database.db'

wordbook = []
header = []

# 防止每次爬取都要读入stopwords
stop_words = set()

with open('stopwords.txt', encoding='utf-8') as f:
    con = f.readlines()
    for i in con:
        i = i.replace("\n", "")  # 去掉读取每一行数据的\n
        stop_words.add(i)


def make_json_response(data, status_code=200):
    response = make_response(json.dumps(data), status_code)
    response.headers["Content-Type"] = "application/json"
    return response

class DB_Operation:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()

    def insert(self,bv,json) ->None:
        sql_str = f"INSERT INTO BV2JSON (BV,JSON) \
            VALUES ('{bv}','{json}')"
        self.c.execute(sql_str)
        self.conn.commit()

    def select(self,bv) ->str:
        cursor = self.c.execute(f"SELECT BV,JSON  from BV2JSON WHERE BV = '{bv}'")
        for row in cursor:
            return row[1]
        return "not found"
    
    def getRandomCookie(self)->str:
        cookie_list = []
        cursor = self.c.execute("SELECT COOKIE  from COOKIES")
        for row in cursor:
            cookie_list.append(row[0])
        return cookie_list[randint(0,len(cookie_list)-1)]
    
dbOperation = DB_Operation()

# 匹配需要被删除的字符串
def strFilter(s:str)->bool:
    if s == '':
        return True
    # 单字重复多次
    if s.replace(s[0],'') == '':
        return True
    return s in stop_words#  or "哈" in s
             

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
    
comment_path = 'bilibili1.csv'
if os.path.exists(comment_path):
    os.remove(comment_path)

# 进行情感分析
@app.route('/test',methods=['POST'])
async def test():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.data)
    bilibili_url=request.json.get('url', "")
    bv_id = bilibili_url
    # bv_id = re.search(r'(BV.*?).{10}', bilibili_url)

    str_list = []

    dbo = DB_Operation()
    db_output = dbo.select(bv_id)
    # 重复请求场景
    if db_output == "not found":
        # 优化并发请求场景，防止并发下文件io异常
        c1 = cbd()
        # 随机获取cookie,也方便运维及时更新cookie库
        c1.cookie = dbo.getRandomCookie()
        c1.stopwords = stop_words
        str_list = list(Counter(c1.search_dm_from_bv(bilibili_url)).items())
        index = 0
        
        while index < len(str_list):
            s = str_list[index][0]
            if strFilter(s):
                str_list.pop(index)
            else:
                index += 1
        str_list = str_list[:min(len(str_list),50)]
        str_list.sort(key = lambda x :  x[1])
        DB_Operation().insert(bv_id,json.dumps(str_list))
    else:
        str_list = json.loads(db_output)


    message="成功"
    prompt = "理解弹幕(str_list)的内容，其中弹幕文字后面对应的数字是弹幕出现的次数，并对内容进行总结概括与情感分析，情感分析不少于100字，不要列举内容"
    return make_json_response({"message":message,"str_list":str_list,"prompt":prompt})

@app.route('/test2',methods=['POST'])
async def test2():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.data)
    bilibili_url=request.json.get('url', "")
    bv_id=bilibili_url
    comment_list=get_comment(bv_id)
    message="成功"
    prompt = "根据评论(str_list)的主要内容，对其进行概括和总结归纳"
    return make_json_response({"message":message,"str_list":comment_list,"prompt":prompt})

def get_comment(bv):
    url=f'https://api.bilibili.com/x/v2/reply?&jsonp=jsonp&pn=1&type=1&oid={bv}&sort=2'
    respond=requests.get(url)
    comment_list=[]
    res_dirct=json.loads(respond.text)
    #print(res_dirct)
    #replys=res_dirct["data"]["replies"][0]["content"]["message"]
    comment_list=extract_comments(res_dirct)
    print(comment_list)
    return comment_list

def extract_comments(data):
    comments_list = []

    def traverse(json_data):
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                if key == "message" and isinstance(value, str):
                    comments_list.append(value)
                else:
                    traverse(value)
        elif isinstance(json_data, list):
            for item in json_data:
                traverse(item)

    traverse(data)
    return comments_list

def spider(cid):
    str_list1=[]
    url = f'https://comment.bilibili.com/{cid}.xml'
    headers = {
        'cookie':"b_lsid=310E7616E_18B7F8BB2C1; _uuid=FBBEDF84-10534-3F4F-CABE-947D7E449510443649infoc; buvid_fp=d82facd6e828f7a0377c00231aa7a3ac; buvid3=9A8D7049-2E3A-1FB4-35F3-E9767149864443888infoc; b_nut=1698651945; buvid4=EE2224ED-C2F7-001B-1982-727B92ACA31843888-023103015-%2FKPDqUY3StH6LeVcWJARtw%3D%3D; enable_web_push=DISABLE; header_theme_version=CLOSE; CURRENT_FNVAL=4048; rpdid=|(JlklRl)~lm0J'uYm)Ylumm); bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTg5MTEyMDAsImlhdCI6MTY5ODY1MTk0MCwicGx0IjotMX0.i-sWHDSCqyeWz2D3RtR20FEI0NnqrjcoBw2Ix1qnLBA; bili_ticket_expires=1698911140; home_feed_column=5; browser_resolution=1872-923; sid=8m6ozd93",
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0'
    }
    resq = requests.get(url, headers=headers)
    resq.encoding = resq.apparent_encoding
    content_list = re.findall('<d p=".*?">(.*?)</d>', resq.text)
    #print(content_list)
    if os.path.exists(comment_path):
        os.remove(comment_path)
    for item in content_list:
        str_list1.append(item)
        with open(comment_path, 'a', encoding='utf-8') as fin:
            fin.write(item + '\n')
        # print(item)
    # print("down")
    return str_list1

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

def chinese_word_cut(mytext):
    # 文本预处理 ：去除一些无用的字符只提取出中文出来
    new_data = re.findall('[\u4e00-\u9fa5]+', mytext, re.S)
    filtered_data = [word for word in new_data if word not in stop_words and "哈" not in word]
    wordcount = Counter(filtered_data).most_common(20)
    print("弹幕数量前二十为：",wordcount)
    return wordcount

def data_visual():
    with open(comment_path, encoding='utf-8') as file:
        comment_text = file.read()
        wordlist = chinese_word_cut(comment_text)
        return wordlist

@app.route('/')
def index():
    return '你是温柔坚强的人吗?'

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8081)