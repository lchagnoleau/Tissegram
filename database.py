# coding=UTF-8

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, DuplicateKeyError

class DataBase(object):
    def __init__(self, ip, port, database, username, password):
        try:
            #open MongoDB server
            self.client = MongoClient(  host=ip,
                                        port=int(port), 
                                        username=username, 
                                        password=password,
                                        authSource=database)


            self.logger.debug("mongo ip is : {}".format(ip))

            #check if connection is well
            self.client.server_info()
        except ServerSelectionTimeoutError:
            exit(0)

        #open database
        self.db = self.client[database]

        #open collection
        self.collection = self.db['users']

    def insert(self, user_id, document):
        try:
            self.collection.update_one({'_id':user_id}, {"$set": document}, upsert=True)
        except DuplicateKeyError:
            pass

    def get_document(self, user_id):
        return self.collection.find_one({"_id": user_id})
