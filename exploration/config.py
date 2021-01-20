import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

SQL_USER = os.getenv('SQL_USER')
SQL_PWD = os.getenv('SQL_PWD')
SQL_HOST = os.getenv('SQL_HOST')
MONGO_HOST = int(os.getenv('MONGO_HOST'))

import pymysql.cursors
from pymongo import MongoClient

sql_inst = pymysql.connect(
    host=SQL_HOST,
    user=SQL_USER,
    password=SQL_PWD
)

mongo_inst = MongoClient('localhost', MONGO_HOST)