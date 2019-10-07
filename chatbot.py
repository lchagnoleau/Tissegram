# coding=UTF-8

import requests
from bottle import Bottle, response, request as bottle_request

HELP = {
    "/help":"Display this message",
    "/welcome":"Display the Welcome message",
    "/addfav":"add a favory",
    "/delfav":"remove a favory",
    "/showfav":"display list of favory",
    "/addalarm":"add an alarm",
    "/delalarm":"remove an alarm",
    "/showalarm":"display list of alarm",
    "/fav fav":"Enter the name of a favory to get the next 5 passages"
}


def welcome_message(name):
    message = "Hi {} !\
        \nI'm Vigilant Sharp and I will help you to not miss your bus. \
        \nTo do this, We will create one or more alarms depending of your needs. \
        \nNext, when your bus will approach from you, I will let know know. \
        \n \
        \nFirst, use command /addfav to ad at least one favory.\
        \nNext, use command /addalarm to add a specific alarm. \
        \n \
        \nFinally, to have the full list of command, use /help\
        \n \
        \nI really hope you will enjoy the service".format(name)
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
    def __init__(self, token, db, transport, *args, **kwargs):
        BotHandlerMixin.__init__(self, token=token)
        Bottle.__init__(self)
        self.db = db
        self.transport = transport
        self.route('/', callback=self.post_handler, method="POST")
    
    def display_help(self, chat_id):
        message = ""
        for key, value in HELP.items():
            message += "{}\n          -> {}\n".format(key, value)

        self.send_message(prepared_data={"chat_id": chat_id,"text": message})

    def add_favory(self, chat_id, command_history={}):
        pass

    def del_favory(self, chat_id, command_history={}):
        pass

    def show_favory(self, chat_id):
        pass

    def add_alarm(self, chat_id, command_history={}):
        pass

    def del_alarm(self, chat_id, command_history={}):
        pass

    def show_alarm(self, chat_id):
        pass

    def show_alarm(self, chat_id):
        pass

    def display_next_passage(self, chat_id, arg):
        if len(arg) != 1:
            self.send_message(prepared_data={"chat_id": chat_id,"text": "You must enter the name of your favory to show its next passages (ex : /fav toto)"})
        else:
            pass

    def post_handler(self):
        data = bottle_request.json
        chat_id = self.get_chat_id(data)
        user_info = self.get_user_info(data)
        message = self.get_message(data)
        arg = message.split(' ')
        command = arg[0]
        arg.pop(0)

        # Check if user is already know and that users data are up to date
        db_doc = self.db.get_document(chat_id)
        if db_doc is None:
            self.db.insert(user_id=chat_id, document={'user-info':user_info,
                'favory':{},
                'alarm':{},
                'command':{'active-command':'None', 'step':0, 'history':[]}
                })
            self.send_message({'chat_id':chat_id, 'text':welcome_message(self.get_user_name(data))})
            return response
        elif db_doc['user-info'] != user_info:
            self.db.insert(user_id=chat_id, document={'user-info':user_info})
            return response

        # Check for command
        if command[0] == '/':
            if command == "/help":
                self.display_help(chat_id=chat_id)
            elif command == "/welcome":
                self.send_message({'chat_id':chat_id, 'text':welcome_message(self.get_user_name(data))})
            elif command == "/addfav":
                self.add_favory(chat_id=chat_id)
            elif command == "/delfav":
                self.del_favory(chat_id=chat_id)
            elif command == "/showfav":
                self.show_favory(chat_id=chat_id)
            elif command == "/addalarm":
                self.add_alarm(chat_id=chat_id)
            elif command == "/delalarm":
                self.del_alarm(chat_id=chat_id)
            elif command == "/showalarm":
                self.show_alarm(chat_id=chat_id)
            elif command == "/fav":
                self.display_next_passage(chat_id=chat_id, arg=arg)
            else:
                self.send_message(prepared_data={"chat_id": chat_id,"text": "Sorry, command unknow. type /help to have list of command."})
        
        # Continue conversation
        else:
            command_history = self.db.get_document(user_id=chat_id)['command']
            if command_history['active-command'] == "/addfav":
                self.add_favory(chat_id=chat_id, command_history=command_history)
            elif command_history['active-command'] == "/delfav":
                self.del_favory(chat_id=chat_id, command_history=command_history)
            elif command_history['active-command'] == "/addalarm":
                self.add_alarm(chat_id=chat_id, command_history=command_history)
            elif command_history['active-command'] == "/delalarm":
                self.del_alarm(chat_id=chat_id, command_history=command_history)
            else:
                self.send_message(prepared_data={"chat_id": chat_id,"text": "Sorry, command unknow. type /help to have list of command."})
    
        return response
