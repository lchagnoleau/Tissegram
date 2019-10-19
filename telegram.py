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
        self.logger.debug("Set data dict at \n{}".format(self.data))

    def is_callback(self):
        if 'callback_query' in self.data.keys():
            self.logger.debug("Message received is a callback")
            return True
        else:
            self.logger.debug("Message received is NOT a callback")
            return False

    def get_chat_id(self):
        chat_id = ""
        if self.is_callback():
            chat_id = self.data['callback_query']['message']['chat']['id']
        else:
            chat_id = self.data['message']['chat']['id']

        self.logger.debug("Chat ID is {}".format(chat_id))
        return chat_id

    def get_callback_id(self):
        callback_query_id = self.data['callback_query']['id']
        self.logger.debug("Callback query ID is {}".format(callback_query_id))
        return callback_query_id

    def get_chat_info(self):
        chat_info = {}
        if self.is_callback():
            chat_info = dict(self.data['callback_query']['message']['chat'])
        else:
            chat_info = dict(self.data['message']['chat'])

        chat_info.pop('id', None)
        self.logger.debug("Chat info is {}".format(chat_info))
        return chat_info

    def get_user_info(self):
        user_info = {}
        if self.is_callback():
            user_info = dict(self.data['callback_query']['from'])
        else:
            user_info = dict(self.data['message']['from'])

        user_info.pop('id', None)
        self.logger.debug("User info is {}".format(user_info))
        return user_info

    def get_user_name(self):
        user_name = self.get_user_info()['first_name']
        self.logger.debug("User name is {}".format(user_name))
        return user_name

    def get_message(self):
        message = self.data['message']['text']
        self.logger.debug("Message is {}".format(message))
        return message

    def get_message_id(self):
        message_id = self.data['message']['message_id']
        self.logger.debug("Message ID is {}".format(message_id))
        return message_id

    def get_callback(self):
        callback = str(self.data['callback_query']['data'])
        self.logger.debug("Callback is {}".format(callback))
        return callback

    def send_message(self, chat_id, message):
        message_url = self.url + 'sendMessage'
        json = {'chat_id':chat_id, 'text':message}
        r = requests.post(message_url, json=json)
        self.logger.debug("Send message at URL : {}\nBody : {}".format(message_url, json))
        self.logger.debug("Response is : \n{}".format(r.json()))
        return r.json()['result']['message_id']

    def send_callback(self, chat_id, message, callback):
        message_url = self.url + 'sendMessage'
        json = {'chat_id':chat_id, 'reply_markup':callback, 'text':message}
        r = requests.post(message_url, json=json)
        self.logger.debug("Send message at URL : {}\nBody : {}".format(message_url, json))
        self.logger.debug("Response is : \n{}".format(r.json()))
        return r.json()['result']['message_id']

    def get_Updates(self, offset=0):
        message_url = self.url + 'getUpdates'
        json = {'offset':offset}
        r = requests.post(message_url, json=json)
        self.logger.debug("Send message at URL : {}\nBody : {}".format(message_url, json))
        self.logger.debug("Response is : \n{}".format(r.json()))
        return r.json()

    def answer_callback(self, callback_id):
        message_url = self.url + 'answerCallbackQuery'
        json = {"callback_query_id": callback_id}
        r = requests.post(message_url, json=json)
        self.logger.debug("Send message at URL : {}\nBody : {}".format(message_url, json))
        self.logger.debug("Response is : \n{}".format(r.json()))

    def delete_message(self, chat_id, message_id):
        message_url = self.url + 'deleteMessage'
        json = {'chat_id':chat_id, 'message_id':message_id}
        r = requests.post(message_url, json=json)
        self.logger.debug("Send message at URL : {}\nBody : {}".format(message_url, json))
        self.logger.debug("Response is : \n{}".format(r.json()))

    def reset_messages(self):
        message_url = self.url + 'deleteWebhook'
        json = {}
        r = requests.post(message_url, json=json)
        self.logger.debug("Send message at URL : {}\nBody : {}".format(message_url, json))
        self.logger.debug("Response is : \n{}".format(r.json()))
        updates = self.get_Updates()

        if len(updates['result']) > 0:
            update_id = 0
            for results in updates['result']:
                if results['update_id'] >= update_id:
                    update_id = results['update_id'] + 1

            updates = self.get_Updates(offset=update_id)

        message_url = self.url + 'setWebhook'
        json = {'url':self.webhook_ip}
        r = requests.post(message_url, json=json)
        self.logger.debug("Send message at URL : {}\nBody : {}".format(message_url, json))
        self.logger.debug("Response is : \n{}".format(r.json()))