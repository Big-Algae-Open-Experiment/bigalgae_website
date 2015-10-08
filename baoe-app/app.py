from flask import Flask
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient()

from routes import *

if __name__ == '__main__':
    db = client[DB_NAME]
    
    global_variable_collection = db[GLOBAL_VARIABLE_COLLECTION]
    
    cache_key_entry = global_variable_collection.find_one({'_id': 'cache_key'})
       
    app.secret_key = cache_key_entry['key_str']
    
    app.run(debug=True)