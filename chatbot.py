# coding=UTF-8

import requests


class Chatbot(object):
    def __init__(self, token):
        self.url = 'https://api.telegram.org/bot{}/'.format(token)

    def get_updates(self):
        return requests.get(url=self.url+'getUpdates').json()