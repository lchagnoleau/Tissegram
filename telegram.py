# coding=UTF-8

import requests
from log import get_logger

class BotHandlerMixin:
    def __init__(self, token, webhook_ip):
        #init logs
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("Init {}".format(self.__class__.__name__))

        self.url = 'https://api.telegram.org/bot{}/'.format(token)
        self.logger.debug("Telegram URL is {}".format(self.url))

        self.data = {}
        self.chat_id = ""
        self.webhook_ip = webhook_ip
        self.logger.debug("Telegram webhook IP is {}".format(self.webhook_ip))

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

    def get_message_id(self):
        return self.data['message']['message_id']

    def get_callback(self):
        return str(self.data['callback_query']['data'])

    def send_message(self, chat_id, message):
        message_url = self.url + 'sendMessage'
        r = requests.post(message_url, json={'chat_id':chat_id, 'text':message})
        return r.json()['result']['message_id']

    def send_callback(self, chat_id, message, callback):
        message_url = self.url + 'sendMessage'
        r = requests.post(message_url, json={'chat_id':chat_id, 'reply_markup':callback, 'text':message})
        return r.json()['result']['message_id']

    def get_Updates(self, offset=0):
        message_url = self.url + 'getUpdates'
        r = requests.post(message_url, json={'offset':offset})
        return r.json()

    def answer_callback(self, callback_id):
        message_url = self.url + 'answerCallbackQuery'
        requests.post(message_url, json={"callback_query_id": callback_id})

    def delete_message(self, chat_id, message_id):
        message_url = self.url + 'deleteMessage'
        requests.post(message_url, json={'chat_id':chat_id, 'message_id':message_id})

    def reset_messages(self):
        message_url = self.url + 'deleteWebhook'
        requests.post(message_url, json={})
        updates = self.get_Updates()

        if len(updates['result']) > 0:
            update_id = 0
            for results in updates['result']:
                if results['update_id'] >= update_id:
                    update_id = results['update_id'] + 1

            updates = self.get_Updates(offset=update_id)

        message_url = self.url + 'setWebhook'
        requests.post(message_url, json={'url':self.webhook_ip})