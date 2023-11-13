# 没数据库的时候运行这个创建一个数据库

import sqlite3
from random import randint
from time import time


class DB_Operation:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()

    def insert(self,bv,json) ->None:
        sql_str = f"INSERT INTO BV2JSON (BV,JSON,DATE) \
            VALUES ('{bv}','{json}',{int(time())})"
        self.c.execute(sql_str)
        self.conn.commit()

    def select(self,bv) ->str:
        cursor = self.c.execute(f"SELECT BV,JSON,DATE from BV2JSON WHERE BV = '{bv}'")
        for row in cursor:
            if int(row[2]) < int(time())-3600*24:
                continue
            return row[1]
        return "not found"
    
    def getRandomCookie(self)->str:
        cookie_list = []
        cursor = self.c.execute("SELECT COOKIE  from COOKIES")
        for row in cursor:
            cookie_list.append(row[0])
        return cookie_list[randint(0,len(cookie_list)-1)]
        
# dbo = DB_Operation()
# # # # dbo.insert("6666","testetst")
# # print(dbo.select("6666"))
# print(dbo.getRandomCookie())

if __name__ == "__main__":
    db_path = './database.db'
    # conn = sqlite3.connect(db_path)
    # c = conn.cursor()
    # c.execute('''CREATE TABLE BV2JSON
    #     (BV TEXT,
    #         JSON TEXT,
    #         DATE INT );''')
    # conn.commit()

    # c.execute('''CREATE TABLE COOKIES
    #     (COOKIE TEXT );''')
    # conn.commit()

    # DB_Operation().insert('12321','12322')
    s = DB_Operation().select("12321")
    print(s)