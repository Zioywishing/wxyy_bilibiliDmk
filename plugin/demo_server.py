#!/usr/env python3
# -*- coding: UTF-8 -*-
import matplotlib as plt
import numpy as np
import jieba
from collections import Counter
from flask import Flask, request, send_file, make_response
from flask_cors import CORS, cross_origin
from getdm import Crawler_Bilibili_Danmu as cbd
# from createDB import DB_Operation
from time import time
import json
import random
import requests
import re
import sqlite3
import os
from random import randint
from threading import Thread

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

    def insert_dmk(self,bv,json) ->None:
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()
        sql_str = f"INSERT INTO BV2DMKJSON (BV,JSON,DATE) \
            VALUES ('{bv}','{json}',{int(time())})"
        self.c.execute(sql_str)
        self.conn.commit()
        self.conn.close()

    def insert_comment(self,bv,json) ->None:
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()
        sql_str = f"INSERT INTO BV2COMMENTJSON (BV,JSON,DATE) \
            VALUES ('{bv}','{json}',{int(time())})"
        self.c.execute(sql_str)
        self.conn.commit()
        self.conn.close()

    def select_dmk(self,bv) ->str:
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()
        cursor = self.c.execute(f"SELECT BV,JSON,DATE from BV2DMKJSON WHERE BV = '{bv}'")
        for row in cursor:
            if int(row[2]) < int(time())-3600*24:
                continue
            self.conn.close()
            return row[1]
        return "not found"
    
    def select_comment(self,bv) ->str:
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()
        cursor = self.c.execute(f"SELECT BV,JSON,DATE from BV2COMMENTJSON WHERE BV = '{bv}'")
        for row in cursor:
            if int(row[2]) < int(time())-3600*24:
                continue
            self.conn.close()
            return row[1]
        return "not found"
    
    def getRandomCookie(self)->str:
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()
        cookie_list = []
        cursor = self.c.execute("SELECT COOKIE  from COOKIES")
        for row in cursor:
            cookie_list.append(row[0])
        self.conn.close()
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
    

@app.route("/.well-known/example.yaml")
async def example_spec():
    with open(".well-known/example.yaml", encoding="utf-8") as f:
        text = f.read()
        return text, 200, {"Content-Type": "text/yaml"}
    
comment_path = 'bilibili1.csv'
if os.path.exists(comment_path):
    os.remove(comment_path)


# 根据BV号获取弹幕库
def getDmk(bv_id):
    str_list = []
    dbo = DB_Operation()
    db_output = dbo.select_dmk(bv_id)
    if db_output == "not found":
        c1 = cbd()
        # 随机获取cookie,也方便运维及时更新cookie库
        # 根本就不用cookie
        # c1.cookie = dbo.getRandomCookie()
        c1.stopwords = stop_words
        str_list = list(Counter(c1.search_dm_from_bv(bv_id)).items())
        # print(str_list)
        index = 0
        while index < len(str_list):
            s = str_list[index][0]
            if strFilter(s):
                str_list.pop(index)
            else:
                index += 1
        str_list = str_list[:min(len(str_list),50)]
        str_list.sort(key = lambda x :  x[1],reverse=True)
        DB_Operation().insert_dmk(bv_id,json.dumps(str_list))
    else:
        str_list = json.loads(db_output)

    print(str_list)
    return str_list

# 根据bv号获取评论
def get_comment(bv_id):
    comment_list=[]
    dbo = DB_Operation()
    db_output = dbo.select_comment(bv_id)
    if db_output == "not found":
        url=f'https://api.bilibili.com/x/v2/reply?&jsonp=jsonp&pn=1&type=1&oid={bv_id}&sort=2'
        respond=requests.get(url)
        res_dirct=json.loads(respond.text)
        comment_list=extract_comments(res_dirct)
        # 选取内容最长的前20条评论
        comment_list.sort(key = lambda x : len(x),reverse=True)
        comment_list = comment_list[:20]
        comment_list = [s[:50] for s in comment_list]  
        DB_Operation().insert_comment(bv_id,json.dumps(comment_list))
    else:
        comment_list = json.loads(db_output)
    print(comment_list)
    return comment_list

# 提取链接中的BV号
def url2bv(url):
    # 提取分享短链中的bv号
    if(url[:15] == "https://b23.tv/"):
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/84.0.4147.89 Safari/537.36",
        }
        data = requests.get(url=url,headers=headers).text[3000:4500]
        data =re.compile('BV\w{10}').search(data)[0]
        return data
    return re.compile('BV\w{10}').search(url)[0]

# 获取视频封面相关
def get_cover(bv_id):
    url = f'https://api.bilibili.com/x/web-interface/view?bvid={bv_id}'
    res = requests.get(url)
    data = json.loads(res.text)
    imageurl = data['data']['pic']
    return imageurl



# 根据关键词进行评论和弹幕分析
@app.route('/analyseKeyword',methods=['POST'])
async def analyseKeyword():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.data)
    keyword=request.json.get('keyword', "")
    bvidList = cbd().search_bvs(keyword,max_size=5)
    comment_list = []
    dmk_list = []
    threadPool = []
    def t_(bv,c,d):
        c+=get_comment(bv)
        d+=getDmk(bv)

    for bv_id in bvidList:
        t = Thread(target=t_,args=[bv_id,comment_list,dmk_list])
        t.start()
        threadPool.append(t)
    for t in threadPool:
        t.join()

    random.shuffle(comment_list)
    random.shuffle(dmk_list)
    comment_list = comment_list[:20]
    dmk_list = dmk_list[:20]
    dmk_list.sort(key = lambda x :  x[1],reverse=True)
    message="成功"
    prompt = "根据弹幕(dmk_list)与评论(comment_list)的主要内容，对内容进行总结概括，分析评论者的情感趋势，给出评论用户群体画像，不少于400字"
    return make_json_response({"message":message,"dm_list":dmk_list,"comment_list":comment_list,"prompt":prompt})

# 进行弹幕分析
@app.route('/analyseDMK',methods=['POST'])
async def analyseDMK():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.data)
    bilibili_url=request.json.get('url', "")
    bv_id = url2bv(bilibili_url)
    str_list = getDmk(bv_id)
    message="成功"
    prompt = "理解弹幕(str_list)的内容，其中弹幕文字后面对应的数字是弹幕出现的次数，并对内容进行总结概括与情感分析，情感分析不少于200字，不要列举内容"
    return make_json_response({"message":message,"str_list":str_list,"prompt":prompt})

# 进行评论分析
@app.route('/analyseComment',methods=['POST'])
async def analyseComment():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.data)
    bilibili_url=request.json.get('url', "")
    bv_id=url2bv(bilibili_url)
    comment_list=get_comment(bv_id)
    message="成功"
    prompt = "根据评论(str_list)的主要内容，对内容进行总结概括，分析评论者的情感趋势，给出评论用户群体画像，不少于200字"
    return make_json_response({"message":message,"str_list":comment_list,"prompt":prompt})

# 进行评论和弹幕分析
@app.route('/analyseBoth',methods=['POST'])
async def analyseBoth():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.data)
    bilibili_url=request.json.get('url', "")
    bv_id = url2bv(bilibili_url)
    comment_list=get_comment(bv_id)
    dmk_list = getDmk(bv_id)
    message="成功"
    prompt = "根据弹幕(dmk_list)与评论(comment_list)的主要内容，对内容进行总结概括，分析评论者的情感趋势，给出评论用户群体画像，不少于400字"
    return make_json_response({"message":message,"dm_list":dmk_list,"comment_list":comment_list,"prompt":prompt})


# 获取视频封面
@app.route('/coverGet',methods=['POST'])
def get_cover_():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.data)
    bilibili_url=request.json.get('url', "")
    bv_id = url2bv(bilibili_url)
    coverurl = get_cover(bv_id)
    message="成功"
    prompt = "获取链接后将链接输出给使用者并告诉使用者这是头像的链接"
    return make_json_response({"message":message,"str_list":coverurl,"prompt":prompt})

# 提取热门词频并分析                ...........
@app.route('/analysehot',methods=['POST'])
async def analysehot():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.data)
    bilibili_url=request.json.get('url', "")
    bv_id = url2bv(bilibili_url)
    comment_list=get_comment(bv_id)
    dmk_list = getDmk(bv_id)
    message="成功"
    prompt = "对弹幕(dmk_list)与评论(comment_list)进行分析,提取其中的出现频率高的词，分析得出关注点，不少于300字"
    return make_json_response({"message":message,"both_list":comment_list+dmk_list,"prompt":prompt})

# 进行弹幕排行
@app.route('/analysePaihang', methods=['POST'])
async def analysePaihang():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.data)
    bilibili_url = request.json.get('url', "")
    bv_id = url2bv(bilibili_url)
    str_list = getDmk(bv_id)
    message = "成功"
    prompt = "对弹幕(str_list)的内容进行分析，其中弹幕文字后面对应的数字是弹幕出现的次数，给出弹幕出现次数最多的前十条弹幕并以直观的方式展现"
    return make_json_response({"message": message, "str_list": str_list, "prompt": prompt})



def extract_comments(data):
    comments_list = []
    def traverse(json_data):
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                if key == "message" and isinstance(value, str):
                    if value[:4] == '回复 @':
                        value = value.split(':',1)[1]
                    comments_list.append(value)
                else:
                    traverse(value)
        elif isinstance(json_data, list):
            for item in json_data:
                traverse(item)

    traverse(data)
    return comments_list

# def spider(cid):
#     str_list1=[]
#     url = f'https://comment.bilibili.com/{cid}.xml'
#     headers = {
#         'cookie':"b_lsid=310E7616E_18B7F8BB2C1; _uuid=FBBEDF84-10534-3F4F-CABE-947D7E449510443649infoc; buvid_fp=d82facd6e828f7a0377c00231aa7a3ac; buvid3=9A8D7049-2E3A-1FB4-35F3-E9767149864443888infoc; b_nut=1698651945; buvid4=EE2224ED-C2F7-001B-1982-727B92ACA31843888-023103015-%2FKPDqUY3StH6LeVcWJARtw%3D%3D; enable_web_push=DISABLE; header_theme_version=CLOSE; CURRENT_FNVAL=4048; rpdid=|(JlklRl)~lm0J'uYm)Ylumm); bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTg5MTEyMDAsImlhdCI6MTY5ODY1MTk0MCwicGx0IjotMX0.i-sWHDSCqyeWz2D3RtR20FEI0NnqrjcoBw2Ix1qnLBA; bili_ticket_expires=1698911140; home_feed_column=5; browser_resolution=1872-923; sid=8m6ozd93",
#         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0'
#     }
#     resq = requests.get(url, headers=headers)
#     resq.encoding = resq.apparent_encoding
#     content_list = re.findall('<d p=".*?">(.*?)</d>', resq.text)
#     #print(content_list)
#     if os.path.exists(comment_path):
#         os.remove(comment_path)
#     for item in content_list:
#         str_list1.append(item)
#         with open(comment_path, 'a', encoding='utf-8') as fin:
#             fin.write(item + '\n')
#         # print(item)
#     # print("down")
#     return str_list1

# def get_cid(BV):
#     print("BV是："+BV)
#     cidurl = f'https://api.bilibili.com/x/player/pagelist?bvid={BV}&jsonp=jsonp'
#     headers = {
#         'cookie':"b_lsid=310E7616E_18B7F8BB2C1; _uuid=FBBEDF84-10534-3F4F-CABE-947D7E449510443649infoc; buvid_fp=d82facd6e828f7a0377c00231aa7a3ac; buvid3=9A8D7049-2E3A-1FB4-35F3-E9767149864443888infoc; b_nut=1698651945; buvid4=EE2224ED-C2F7-001B-1982-727B92ACA31843888-023103015-%2FKPDqUY3StH6LeVcWJARtw%3D%3D; enable_web_push=DISABLE; header_theme_version=CLOSE; CURRENT_FNVAL=4048; sid=nvzw4wae; rpdid=|(JlklRl)~lm0J'uYm)Ylumm); bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTg5MTEyMDAsImlhdCI6MTY5ODY1MTk0MCwicGx0IjotMX0.i-sWHDSCqyeWz2D3RtR20FEI0NnqrjcoBw2Ix1qnLBA; bili_ticket_expires=1698911140; home_feed_column=5; browser_resolution=1872-923",
#         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0'
#     }
#     cidres = requests.get(cidurl, headers=headers)
#     print(cidres.json())
#     cid = cidres.json()['data'][0]['cid']
#     # print(cid)
#     return cid

# def chinese_word_cut(mytext):
#     # 文本预处理 ：去除一些无用的字符只提取出中文出来
#     new_data = re.findall('[\u4e00-\u9fa5]+', mytext, re.S)
#     filtered_data = [word for word in new_data if word not in stop_words and "哈" not in word]
#     wordcount = Counter(filtered_data).most_common(20)
#     print("弹幕数量前二十为：",wordcount)
#     return wordcount

# def data_visual():
#     with open(comment_path, encoding='utf-8') as file:
#         comment_text = file.read()
#         wordlist = chinese_word_cut(comment_text)
#         return wordlist

@app.route('/')
def index():
    return '你是温柔坚强的人吗?'

def runHttp():
    app.run(debug=True, host='0.0.0.0', port=8081)

def runHttps():
    ssl_context=('miaospring.top_bundle.pem', 'miaospring.top.key')
    app.run(debug=True, host='0.0.0.0', port=8081, ssl_context=ssl_context)

if __name__ == '__main__':
    runHttp()