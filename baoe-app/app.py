from flask import Flask
from pymongo import MongoClient

import logging, sys

app = Flask(__name__)

client = MongoClient()

from routes import *

logging.basicConfig(stream=sys.stderr)

db = client[DB_NAME]

global_variable_collection = db[GLOBAL_VARIABLE_COLLECTION]

cache_key_entry = global_variable_collection.find_one({'_id': 'cache_key'})
    
app.secret_key = cache_key_entry['key_str']

if __name__ == '__main__':
    app.run(debug=True)