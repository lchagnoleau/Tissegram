# coding=UTF-8

import requests

class BotHandlerMixin:
    def __init__(self, token):
        self.url = 'https://api.telegram.org/bot{}/'.format(token)
        self.data = {}
        self.chat_id = ""

    def set_data(self, data):
        self.data.clear()
        self.data = dict(data)

    def is_callback(self):
        if 'callback_query' in self.data.keys():
            return True
        else:
            return False

    def get_chat_id(self):
        if self.is_callback():
            return self.data['callback_query']['message']['chat']['id']
        else:
            return self.data['message']['chat']['id']

    def get_callback_id(self):
        return self.data['callback_query']['id']

    def get_chat_info(self):
        chat_info = {}
        if self.is_callback():
            chat_info = dict(self.data['callback_query']['message']['chat'])
        else:
            chat_info = dict(self.data['message']['chat'])

        chat_info.pop('id', None)
        return chat_info

    def get_user_info(self):
        user_info = {}
        if self.is_callback():
            user_info = dict(self.data['callback_query']['from'])
        else:
            user_info = dict(self.data['message']['from'])

        user_info.pop('id', None)
        return user_info

    def get_user_name(self):
        return self.get_user_info()['first_name']

    def get_message(self):
        return self.data['message']['text']

    def get_callback(self):
        return self.data['callback_query']['self.data']

    def send_message(self, chat_id, message):
        message_url = self.url + 'sendMessage'
        requests.post(message_url, json={'chat_id':chat_id, 'text':message})

    def send_callback(self, chat_id, message, callback):
        message_url = self.url + 'sendMessage'
        requests.post(message_url, json={'chat_id':chat_id, 'reply_markup':callback, 'text':message})

    def answer_callback(self, callback_id):
        message_url = self.url + 'answerCallbackQuery'
        requests.post(message_url, json={"callback_query_id": callback_id})