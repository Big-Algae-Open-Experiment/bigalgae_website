#!/bin/python

try:
    from pymongo import MongoClient
except ImportError:
    import os

    PROJECT_DIR = '/var/www/html/baoe-app'

    activate_this = os.path.join(PROJECT_DIR, 'env', 'bin', 'activate_this.py')
    execfile(activate_this, dict(__file__=activate_this))
    from pymongo import MongoClient
    
    
client = MongoClient()

DB_NAME = 'bigalgae'

BIOREACTOR_COLLECTION = 'bioreactors'

GLOBAL_VARIABLE_COLLECTION = 'counter'

# deletes all databases currently created
for database in client.database_names():
    client.drop_database(database)

db = client[DB_NAME]

variable_collection = db[GLOBAL_VARIABLE_COLLECTION]

variable_collection.insert({'_id': 'counter', \
                            'seq': 0})
                        
variable_collection.insert({'_id': 'cache_key', \
                            'key_str': 'asdhHASDKh!!*&%SASDKH8723as112'})