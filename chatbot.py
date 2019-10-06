# coding=UTF-8

import requests
from bottle import Bottle, response, request as bottle_request


class BotHandlerMixin:
    def __init__(self, token):
        self.url = 'https://api.telegram.org/bot{}/'.format(token)

    def get_chat_id(self, data):
        chat_id = data['message']['chat']['id']
        return chat_id

    def get_message(self, data):
        message_text = data['message']['text']
        return message_text

    def send_message(self, prepared_data):
        message_url = self.url + 'sendMessage'
        print(message_url)
        requests.post(message_url, json=prepared_data)
        
    def get_updates(self):
        return requests.get(url=self.url+'getUpdates').json()

class Chatbot(BotHandlerMixin, Bottle): 
    def __init__(self, token, *args, **kwargs):
        BotHandlerMixin.__init__(self, token=token)
        Bottle.__init__(self)
        self.route('/', callback=self.post_handler, method="POST")

    def change_text_message(self, text):
        return text[::-1]

    def prepare_data_for_answer(self, data):
        message = self.get_message(data)
        answer = self.change_text_message(message)
        chat_id = self.get_chat_id(data)
        json_data = {
            "chat_id": chat_id,
            "text": answer,
        }
        return json_data

    def post_handler(self):
        data = bottle_request.json
        answer_data = self.prepare_data_for_answer(data)
        self.send_message(answer_data)
        return response
