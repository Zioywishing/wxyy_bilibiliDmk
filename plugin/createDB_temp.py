# 没数据库的时候运行这个创建一个数据库

import sqlite3
from random import randint

db_path = './database.db'
# conn = sqlite3.connect(db_path)
# c = conn.cursor()
# c.execute('''CREATE TABLE BV2JSON
#        (BV TEXT,
#        JSON TEXT );''')
# conn.commit()

# c.execute('''CREATE TABLE COOKIES
#        (COOKIE TEXT );''')
# conn.commit()

# sql_str = f'''INSERT INTO COOKIES (COOKIE) VALUES ("b_lsid=310E7616E_18B7F8BB2C1; _uuid=FBBEDF84-10534-3F4F-CABE-947D7E449510443649infoc; buvid_fp=d82facd6e828f7a0377c00231aa7a3ac; buvid3=9A8D7049-2E3A-1FB4-35F3-E9767149864443888infoc; b_nut=1698651945; buvid4=EE2224ED-C2F7-001B-1982-727B92ACA31843888-023103015-%2FKPDqUY3StH6LeVcWJARtw%3D%3D; enable_web_push=DISABLE; header_theme_version=CLOSE; CURRENT_FNVAL=4048; rpdid=|(JlklRl)~lm0J'uYm)Ylumm); bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTg5MTEyMDAsImlhdCI6MTY5ODY1MTk0MCwicGx0IjotMX0.i-sWHDSCqyeWz2D3RtR20FEI0NnqrjcoBw2Ix1qnLBA; bili_ticket_expires=1698911140; home_feed_column=5; browser_resolution=1872-923; sid=8m6ozd93")'''
# c.execute(sql_str)
# conn.commit()
# conn.close()

# class DB_Operation:
#     def __init__(self) -> None:
#         self.conn = sqlite3.connect(db_path)
#         self.c = self.conn.cursor()

#     def insert(self,bv,json) ->None:
#         sql_str = f"INSERT INTO BV2JSON (BV,JSON) \
#             VALUES ('{bv}','{json}')"
#         self.c.execute(sql_str)
#         self.conn.commit()

#     def select(self,bv) ->str:
#         cursor = self.c.execute(f"SELECT BV,JSON  from BV2JSON WHERE BV = '{bv}'")
#         for row in cursor:
#             return row[1]
#         return "not found"
    
#     def getRandomCookie(self)->str:
#         cookie_list = []
#         cursor = self.c.execute("SELECT COOKIE  from COOKIES")
#         for row in cursor:
#             cookie_list.append(row[0])
#         return cookie_list[randint(0,len(cookie_list)-1)]
        
# dbo = DB_Operation()
# # # # dbo.insert("6666","testetst")
# # print(dbo.select("6666"))
# print(dbo.getRandomCookie())