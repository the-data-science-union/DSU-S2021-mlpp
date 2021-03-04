import os
from os.path import join, dirname
from dotenv import load_dotenv
from pymongo import MongoClient

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

ATLAS_CONNECTION_STRING = os.getenv('ATLAS_CONNECTION_STRING')

client = MongoClient(ATLAS_CONNECTION_STRING)