# 清空数据库中BV号对应搜索结果

import sqlite3
from random import randint

db_path = './database.db'

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute('''DELETE FROM BV2DMKJSON''')
c.execute('''DELETE FROM BV2COMMENTJSON''')
conn.commit()