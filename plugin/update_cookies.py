# 根据cookies_path中的内容更新database中的cookies

import sqlite3
from random import randint
import os

db_path = './database.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute('''DELETE FROM BV2JSON''')
conn.commit()

# 以行分隔
cookies_path = "./cookies.txt"

cookies = open  (cookies_path,  "r")

for s in cookies:
    sql_str = f'''INSERT INTO COOKIES (COOKIE) VALUES ("{s}")'''
    c.execute(sql_str)
    conn.commit()
conn.close()

