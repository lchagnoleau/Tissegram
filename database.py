# coding=UTF-8

from log import *
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, DuplicateKeyError

class DataBase(object):
    def __init__(self, ip, port, database, username, password):
        #init logs
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("Init database")

        #open dataBase
        self.logger.debug("Open MongoDB database \"{0}\" at : {1}:{2}".format(database, ip, port))

        try:
            #open MongoDB server
            self.client = MongoClient('mongodb://%s:%s@%s:%s' % (username, password, ip, port))

            #check if connection is well
            self.client.server_info()
        except ServerSelectionTimeoutError as err:
            self.logger.error(err)
            exit(0)

        #open database
        self.db = self.client[database]

        #open collection
        self.collection = self.db['users']

    def insert(self, chat_id, document):
        try:
            self.collection.update_one({'_id':chat_id}, {"$set": document}, upsert=True)
        except DuplicateKeyError as err:
            self.logger.error(err)
