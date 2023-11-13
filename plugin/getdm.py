import urllib.parse
import urllib.request
import json
from threading import Thread, Lock
from bs4 import BeautifulSoup as bs
import requests
import re
import jieba
import wordcloud
import os
from re import match
import pandas as pd
import time
import logging
import sqlite3
db_path = './database.db'
from random import randint

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




class Crawler_Bilibili_Danmu:
    def __init__(self):
        # 自己设置

        # 关闭jieba库的日志输出
        jieba.setLogLevel(logging.INFO)

        # 对象运行需要,用于多线程任务
        self.keyword = ''
        self.cids = set()
        self.bvs = []
        self.dms = []
        self.stopwords = set()
        self.count = 0
        self.size = 0

        # # 读入stopwords
        # try:
        #     with open('.\\stopwords.txt', encoding='utf-8') as src:
        #         for word in src:
        #             word = word.strip()
        #             self.stopwords.add(word)
        # except:
        #     pass

        # 检查是否存在并创建output文件夹用于存放
        # output_exist_flag = False
        # for path in os.listdir('./'):
        #     # check if current path is a file
        #     if os.path.isdir(os.path.join('./', path)) and path == 'output':
        #         output_exist_flag = True
        #         break
        # if output_exist_flag == False:
        #     os.mkdir('./output')

        # cookie请自己赋值
        self.cookie = ''


    # 重新初始化对象
    def reinit(self):
        del self.cids
        del self.bvs
        del self.dms
        del self.count
        del self.size
        self.cids = set()
        self.bvs = []
        self.dms = []
        self.count = 0
        self.size = 0

    # 弃用
    # def thread_cids_add_from_bv(self, bv, lock):
    #     cid = self.get_cid(bv)
    #     lock.acquire()
    #     self.cids.add(cid)
    #     print('cids.add:', cid, 'len(cids)=', len(self.cids))
    #     lock.release()

    # 指定keyword, page, order, lock, 获取对应搜索结果的bv号并存放于self.bvs
    def thread_get_bvs(self, keyword, page, order, lock):
        try:
            if page >= 25:
                return
            url = 'https://api.bilibili.com/x/web-interface/wbi/search/type?&page_size=42&search_type=video&keyword=' + \
                str(keyword) + '&page='+str(page) + '&order=' + order
            print(url)
            headers = {
                'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/84.0.4147.89 Safari/537.36",
            }
            headers['cookie'] = self.cookie
            data = requests.get(url=url, headers=headers).text
            BVs = re.findall('BV..........', data)
            lock.acquire()
            try:
                for bvid in BVs:
                    self.bvs.append(bvid)
                lock.release()
            except Exception as err:
                print(err)
                lock.release()
                return None
        except Exception as err:
            print(err)
            return None

    # 指定bv号, 获取对应视频的所有弹幕并存放于self.dms
    def thread_dms_add_from_bv(self, bv, lock):
        try:
            cid = self.get_cid(bv)
            if cid != None:
                dms = self.get_dm(cid)
                if dms != None:
                    lock.acquire()
                    # print('cid=', cid, "add_dms_sum_=", len(dms))
                    try:
                        self.dms += dms
                        self.count += 1
                        # if int(self.count * 100/self.size) > int((self.count - 1) * 100/self.size):
                        #     print('爬取弹幕进度：' +
                        #           str(int(0.1+self.count/self.size*100)) + '%')
                        lock.release()
                    except Exception as err:
                        lock.release()
                        print(err)
                        return None
        except Exception as err:
            print(err)
            return None

    # 输入oid号，返回该视频所有弹幕组成的list，若出错则返回None
    def get_dm(self, oid):
        try:
            if type(oid) != 'string':
                oid = str(oid)
            url = 'https://api.bilibili.com/x/v1/dm/list.so?oid=' + oid
            data = requests.get(url=url)
            data.encoding = 'utf-8'
            data = data.text
            soup = bs(data)
            data = soup.find_all('d')
            res = []
            for i, t in enumerate(data):
                res.append(t.text)
            return res
        except Exception as err:
            print(err)
            return None

    # 弃用
    # def get_bvs(self, keyword, page=1):
    #     try:
    #         url = 'https://api.bilibili.com/x/web-interface/wbi/search/type?&page_size=42&search_type=video&keyword=' + \
    #             str(keyword) + '&page='+str(page)
    #         print(url)
    #         headers = {
    #             'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    #             "Chrome/84.0.4147.89 Safari/537.36",
    #         }
    #         headers['cookie'] = self.cookie
    #         data = requests.get(url=url, headers=headers).text
    #         BVs = re.findall('BV..........', data)
    #         BVs = sorted(set(BVs))
    #         return BVs
    #     except Exception as err:
    #         print(err)
    #         return None

    # 将bv号转为cid，cid与oid等价
    def get_cid(self, bvid):
        try:
            url = "https://api.bilibili.com/x/player/pagelist?bvid="+bvid+"&jsonp=jsonp"
            html = urllib.request.urlopen(url)
            html = html.read()
            html = json.loads(html)
            return html['data'][0]['cid']
        except Exception as err:
            print(err)
            return None

    # 将列表写入xls文件
    def list2xlsx(self, data, name):

        # 当data数量过大时进行切片
        if len(data) > 1000000:
            i = 1
            while 1000000*i < len(data):
                self.list2xlsx(data[(i-1)*1000000:i*1000000],name + '_part' + str(i))
                i += 1
            self.list2xlsx(data[(i-1)*1000000:i*1000000],name + '_part' + str(i))
            return
        
        pf = pd.DataFrame(data)
        # 指定生成的Excel表格名称
        file_path = pd.ExcelWriter('./output/'+name+'.xlsx')
        # 输出
        pf.to_excel(file_path, encoding='utf-8', index=False,engine='openpyxl')
        # 保存表格
        file_path.save()

    # 将字典写入xls文件
    def dict2xlsx(self, data, name):

        # 当data数量过大时进行切片
        if len(data) > 1000000:
            data = list(data)
            i = 1
            while 1000000*i < len(data):
                self.dict2xlsx(data[(i-1)*1000000:i*1000000],name + '_part' + str(i))
                i += 1
            self.dict2xlsx(data[(i-1)*1000000:i*1000000],name + '_part' + str(i))
            return
        
        # 将字典列表转换为DataFrame
        pf = pd.DataFrame(list(data))
        # 指定生成的Excel表格名称
        file_path = pd.ExcelWriter('./output/'+name+'.xlsx')
        # 输出
        pf.to_excel(file_path, encoding='utf-8', index=False)
        # 保存表格
        file_path.save()

    # 将列表写入csv文件
    def list2csv(self, data, name):
        pf = pd.DataFrame(data)
        # 指定名称
        file_path = './output/'+name+'.csv'
        # 输出
        pf.to_csv(file_path, encoding='utf-8', index=False)

    # 将字典写入xls文件
    def dict2csv(self, data, name):
        # 将字典列表转换为DataFrame
        pf = pd.DataFrame(list(data))
        # 指定生成的Excel表格名称
        file_path = './output/'+name+'.csv'
        # 输出
        pf.to_csv(file_path, encoding='utf-8', index=False)

    # 获取string类型格式化的时间
    def get_time(self):
        return time.strftime('%Y%m%d', time.localtime())
    
    #前20最多的弹幕，任务要求
    def qian20(self,dms):
        dmk = {}
        for i in dms:
            if i not in dmk:
                dmk[i] = 1
            else:
                dmk[i] += 1
        return sorted(dmk.items(),key=lambda x: x[1], reverse=True)[:min(len(dmk),20)]

    # 输入关键词keyword,最大爬取视频数量（可选，默认为1）,返回根据搜索结果而爬取的至多max_size个视频的所有弹幕，list类型。
    def search_dm(self, keyword, max_size=1) -> list:
        try:
            self.keyword = keyword
            bvs = set()
            lock = Lock()
            threads = set()

            # 获取bv号，当需要的bv号超过1000个时，尝试使用其他搜索order来获取更多bv号
            for ord in ['default', 'ranklevel', 'click', 'scores', 'damku', 'stow', 'pubdate', 'senddate', 'id']:

            # 获取bv号，作业需求修正
            # for ord in ['default']:
                for num in range(min(int(max_size/40)+1, 25)):
                    t = Thread(target=self.thread_get_bvs,
                               args=(keyword, num+1, ord, lock))
                    t.start()
                    threads.add(t)
                while len(threads) > 0:
                    threads.pop().join()
                if len(set(self.bvs)) >= max_size:
                    break

            # 显示进度用
            self.size = len(set(self.bvs))
            print('共采集到'+str(self.size)+'个BV号')

            # 对于每个bv号，创建一个线程用于获取bv号对应视频的弹幕
            for bvid in self.bvs:
                if bvid not in bvs:
                    bvs.add(bvid)
                    t = Thread(target=self.thread_dms_add_from_bv,
                               args=(bvid, lock))
                    t.start()
                    threads.add(t)
                    if len(bvs) == max_size:
                        break
            self.size = len(bvs)
            while len(threads) > 0:
                threads.pop().join()

            dms = self.dms[:]
            print('爬取弹幕总数:', len(dms))
            # self.reinit()
            return dms
        except Exception as e:
            print(e)
            return []
    
    # 输入bv号,最大爬取视频数量（可选，默认为1）,返回视频的所有弹幕，list类型。
    def search_dm_from_bv(self, bvid) -> list:
        try:
            bvid = re.compile('BV\w{10}').search(bvid)[0]
            lock = Lock()
            t = Thread(target=self.thread_dms_add_from_bv,
                               args=(bvid, lock))
            t.start()
            t.join()

            dms = self.dms[:]
            # print('爬取弹幕总数:', len(dms))
            # self.reinit()
            return dms
        except Exception as e:
            print(e)
            return []



    #输入list类型的弹幕,根据弹幕将其转换为xlsx文件和wordcloud图片
    def process_dms(self, dms, keyword = None):
        print(keyword)
        if keyword == None or type(keyword) != type('miao'):
            keyword = self.keyword
        word_count = {}
        len_dms = len(dms)
        for i, s in enumerate(dms):
            s1 = ''.join(re.findall('[\u4e00-\u9fa5]', s))
            for w in jieba.lcut(s1):
                if w in self.stopwords or len(w) == 1 or '哈' in w:
                    continue
                if w not in word_count:
                    word_count[w] = 1
                else:
                    word_count[w] += 1
            if int(i * 100/len_dms) > int((i - 1) * 100/len_dms):
                print('处理弹幕进度：' +
                      str(int(0.1+i * 100/len_dms)) + '%')
        word_count = sorted(word_count.items(),
                            key=lambda x: x[1], reverse=True)
        self.dict2xlsx(word_count, keyword+'_WordCount_'+self.get_time())
        # self.dict2csv(word_count, keyword+'_WordCount_'+self.get_time())

        # max_words_num = 300
        # index = 0.5
        # text = {}
        # for w in word_count[:max(len(word_count), max_words_num)]:
        #     text[w[0]] = w[1]
        # wc = wordcloud.WordCloud(font_path="msyh.ttc",
        #                          width=int(1920*index),
        #                          height=int(1080*index),
        #                          background_color='white',
        #                          max_words=max_words_num,
        #                          relative_scaling=0.5,
        #                          min_font_size=1,
        #                          prefer_horizontal=1
        #                          #  stopwords=s
        #                          )
        # wc.generate_from_frequencies(text)
        # file_name = keyword + '_' + self.get_time() + '.png'
        # wc.to_file('./output/'+file_name)


        # plt.imshow(wc, interpolation='bilinear')  # 用plt显示图片
        # plt.axis("off")  # 不显示坐标轴
        # plt.show()  # 显示图片

    def getRank(self) -> map:
        dms = self.dms[:]
        word_count = {}
        # len_dms = len(dms)
        for i, s in enumerate(dms):
            s1 = ''.join(re.findall('[\u4e00-\u9fa5]', s))
            for w in jieba.lcut(s1):
                if w in self.stopwords or len(w) == 1 or '哈' in w:
                    continue
                if w not in word_count:
                    word_count[w] = 1
                else:
                    word_count[w] += 1
            # if int(i * 100/len_dms) > int((i - 1) * 100/len_dms):
            #     print('处理弹幕进度：' +
            #         str(int(0.1+i * 100/len_dms)) + '%')
        word_count = sorted(word_count.items(),
                            key=lambda x: x[1], reverse=True)
        return word_count


# 使用
if __name__ == '__main__':
    c = Crawler_Bilibili_Danmu()
    
    c.cookie = DB_Operation().getRandomCookie()

    # # 通过keyword查询

    # print('------------------------------------------------------')
    # keyword = '黑色柳丁'
    # c.search_dm(keyword, 3)
    # print(c.getRank())

    
    c.reinit()

    # 通过bv号查询
    print('------------------------------------------------------')
    bv = 'https://www.bilibili.com/video/BV11N4y1S7MN/?spm_id_from=333.1007.tianma.1-3-3.click'
    c.search_dm_from_bv(bv)
    print(c.getRank())

