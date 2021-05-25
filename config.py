import os
from os.path import join, dirname
from dotenv import load_dotenv
from pymongo import MongoClient
import pymysql.cursors

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

client = MongoClient('localhost', 27017, username='admin', password="dsumlppftw")

sql_client = lambda db: pymysql.connect(host = 'localhost',
                             user='root',
                             password='NvbAvnm#R^f9f3',
                             database=db)