SQL_USER = 'root'
SQL_PWD = 'Qw3rty11'
SQL_HOST = '127.0.0.1'
MONGO_HOST = 27017

## Only edit above this line ##

import pymysql.cursors
from pymongo import MongoClient

sql_inst = pymysql.connect(
    host=SQL_HOST,
    user=SQL_USER,
    password=SQL_PWD
)

mongo_inst = MongoClient('localhost', MONGO_HOST)