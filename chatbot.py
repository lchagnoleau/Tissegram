# coding=UTF-8

import requests
from bottle import Bottle, response, request as bottle_request


def welcome_message(name):
    message = "Hi {}".format(name)
    return message

class BotHandlerMixin:
    def __init__(self, token):
        self.url = 'https://api.telegram.org/bot{}/'.format(token)

    def get_chat_id(self, data):
        chat_id = data['message']['chat']['id']
        return chat_id

    def get_chat_info(self, data):
        chat_info = dict(data['message']['chat'])
        chat_info.pop('id', None)
        return chat_info

    def get_user_info(self, data):
        user_info = dict(data['message']['from'])
        user_info.pop('id', None)
        return user_info

    def get_user_name(self, data):
        user_name = ""
        try:
            user_name = data['message']['from']['first_name']
        except:
            pass
        return user_name

    def get_message(self, data):
        message_text = data['message']['text']
        return message_text

    def send_message(self, prepared_data):
        message_url = self.url + 'sendMessage'
        print(prepared_data)
        print(message_url)
        requests.post(message_url, json=prepared_data)
        
    def get_updates(self):
        return requests.get(url=self.url+'getUpdates').json()

class Chatbot(BotHandlerMixin, Bottle): 
    def __init__(self, token, db, *args, **kwargs):
        BotHandlerMixin.__init__(self, token=token)
        Bottle.__init__(self)
        self.db = db
        self.route('/', callback=self.post_handler, method="POST")

    def post_handler(self):
        data = bottle_request.json
        chat_id = self.get_chat_id(data)
        user_info = self.get_user_info(data)

        # Check if user is already know and that users data are up to date
        db_doc = self.db.get_document(chat_id)
        if db_doc is None:
            self.db.insert(chat_id=chat_id, document={'user-info':user_info})
            self.send_message({'chat_id':chat_id, 'text':welcome_message(self.get_user_name(data))})
        elif db_doc['user-info'] != user_info:
            self.db.insert(chat_id=chat_id, document={'user-info':user_info})

        return response
