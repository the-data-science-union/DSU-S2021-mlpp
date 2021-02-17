from pymongo import MongoClient
import pymysql.cursors
import os
from os.path import join, dirname
from dotenv import load_dotenv
from pymysql.constants import CLIENT

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

SQL_USER = os.getenv('SQL_USER')
SQL_PWD = os.getenv('SQL_PWD')
SQL_HOST = os.getenv('SQL_HOST')
MONGO_HOST = int(os.getenv('MONGO_HOST'))


def sql_inst(db=None):
    return pymysql.connect(
        host=SQL_HOST,
        user=SQL_USER,
        password=SQL_PWD,
        database=db,
        client_flag=CLIENT.MULTI_STATEMENTS
    )


mongo_inst = MongoClient('localhost', MONGO_HOST)
