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
        try:
            chat_id = data['message']['chat']['id']
        except:
            chat_id = data['callback_query']['message']['chat']['id']
        return chat_id

    def get_callback_id(self, data):
        try:
            callback_id = data['callback_query']['id']
        except:
            callback_id = ""
        return callback_id

    def get_chat_info(self, data):
        try:
            chat_info = dict(data['message']['chat'])
        except:
            chat_info = dict(data['callback_query']['message']['chat'])
        chat_info.pop('id', None)
        return chat_info

    def get_user_info(self, data):
        try:
            user_info = dict(data['message']['from'])
        except:
            user_info = dict(data['callback_query']['from'])
        user_info.pop('id', None)
        return user_info

    def get_user_name(self, data):
        user_name = ""
        try:
            user_name = self.get_user_info()['first_name']
        except:
            pass
        return user_name

    def get_message(self, data):
        try:
            message_text = data['message']['text']
        except:
            message_text = data['callback_query']['data']
        return message_text

    def send_message(self, prepared_data):
        message_url = self.url + 'sendMessage'
        requests.post(message_url, json=prepared_data)

    def answer_callback(self, prepared_data):
        message_url = self.url + 'answerCallbackQuery'
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

    def add_favory(self, chat_id, command_history={}, message="", callback_id=""):
        step = command_history['step']
        history = dict(command_history['history'])
        active = "/addfav"

        if step == 0:
            return_message = "Ok, we will add a new favory together.\
                \nFirst, tell me approximately the name of the stop area"

            self.send_message(prepared_data={"chat_id": chat_id,"text": return_message})
            step += 1

        elif step == 1:
            places = self.transport.get_places(term=message)
            if len(places) > 0:
                return_message = "Well. Now, selected the correct area in the list below:\n"
                callback = {"inline_keyboard":[]}
                for place in places:
                    callback["inline_keyboard"].append([{"text":place[1], "callback_data":place[0]}])

                self.send_message(prepared_data={"chat_id": chat_id, "reply_markup":callback, "text": return_message})
                step += 1
            
            else:
                return_message = "Sorry, no input matches with your request. Can you try again:"
                self.send_message(prepared_data={"chat_id": chat_id, "text": return_message})

        elif step == 2:
            self.answer_callback(prepared_data={"callback_query_id": callback_id})
            lines = self.transport.get_lines_by_stoppoints(stopId=message)
            if len(lines) > 0:
                return_message = "Select the line:\n"
                callback = {"inline_keyboard":[]}
                text = ""
                i = 0
                history["line-selection"] = []
                for line in lines:
                    text = "line {} direction {}".format(line[0], line[1])
                    callback["inline_keyboard"].append([{"text":text, "callback_data":str(i)}])
                    history["line-selection"].append(line)
                    i += 1

                self.send_message(prepared_data={"chat_id": chat_id, "reply_markup":callback, "text": return_message})
                step += 1
            
            else:
                return_message = "Sorry, there are no lines for this area..."
                self.send_message(prepared_data={"chat_id": chat_id, "text": return_message})
                active = "None"
                step = 0

        elif step == 3:
            self.answer_callback(prepared_data={"callback_query_id": callback_id})
            history["line-selected"] = history["line-selection"][int(message)]
            self.send_message(prepared_data={"chat_id": chat_id, "text": "Finaly, give a name for your favory:"})
            step += 1

        elif step == 4:
            line = self.db.get_document(user_id = chat_id)["command"]["history"]["line-selected"]
            l = {
                "line":line[0],
                "destination":line[1],
                "destination-id":line[2]
            }
            favory = self.db.get_document(user_id = chat_id)["favory"]
            if message not in favory.keys():
                favory[message] = l
                self.db.insert(user_id=chat_id, document={'favory':favory})
                self.send_message(prepared_data={"chat_id": chat_id, "text": "Congratulation, your favory {} is succesfully saved !".format(message)})
                active = "None"
                step = 0
                history.clear()

            else:
                self.send_message(prepared_data={"chat_id": chat_id, "text": "Name {} is already used. Please select another name:".format(message)})


        self.db.insert(user_id=chat_id, document={'command':{'active-command':active, 'step':step, 'history':history}})

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
        favory = self.db.get_document(user_id=chat_id)['favory']
        if len(arg) != 1:
            self.send_message(prepared_data={"chat_id": chat_id,"text": "You must enter the name of your favory to show its next passages (ex : /fav toto)"})
        elif arg[0] not in favory:
            self.send_message(prepared_data={"chat_id": chat_id,"text": "You must enter a valid name of your favory to show its next passages (ex : /fav toto)"})
        else:
            pass

    def post_handler(self):
        data = bottle_request.json
        chat_id = self.get_chat_id(data)
        message = self.get_message(data)
        arg = message.split(' ')
        command = arg[0]
        user_info = self.get_user_info(data)
        callback_id = self.get_callback_id(data)
        arg.pop(0)

        # Check if user is already know and that users data are up to date
        db_doc = self.db.get_document(chat_id)
        if db_doc is None:
            self.db.insert(user_id=chat_id, document={'user-info':user_info,
                'favory':{},
                'alarm':{},
                'command':{'active-command':'None', 'step':0, 'history':{}}
                })
            self.send_message({'chat_id':chat_id, 'text':welcome_message(self.get_user_name(data))})
            return response
        elif db_doc['user-info'] != user_info:
            self.db.insert(user_id=chat_id, document={'user-info':user_info})

        # Check for command
        if command[0] == '/':
            self.db.insert(user_id=chat_id, document={'command':{'active-command':'None', 'step':0, 'history':{}}})
            command_history = self.db.get_document(user_id=chat_id)['command']
            if command == "/help":
                self.display_help(chat_id=chat_id)
            elif command == "/welcome":
                self.send_message({'chat_id':chat_id, 'text':welcome_message(self.get_user_name(data))})
            elif command == "/addfav":
                self.add_favory(chat_id=chat_id, command_history=command_history)
            elif command == "/delfav":
                self.del_favory(chat_id=chat_id, command_history=command_history)
            elif command == "/showfav":
                self.show_favory(chat_id=chat_id, command_history=command_history)
            elif command == "/addalarm":
                self.add_alarm(chat_id=chat_id, command_history=command_history)
            elif command == "/delalarm":
                self.del_alarm(chat_id=chat_id, command_history=command_history)
            elif command == "/showalarm":
                self.show_alarm(chat_id=chat_id, command_history=command_history)
            elif command == "/fav":
                self.display_next_passage(chat_id=chat_id, arg=arg)
            else:
                self.send_message(prepared_data={"chat_id": chat_id,"text": "Sorry, command unknow. type /help to have list of command."})
    
        # Continue conversation
        else:
            command_history = self.db.get_document(user_id=chat_id)['command']
            if command_history['active-command'] == "/addfav":
                self.add_favory(chat_id=chat_id, command_history=command_history, message=message, callback_id=callback_id)
            elif command_history['active-command'] == "/delfav":
                self.del_favory(chat_id=chat_id, command_history=command_history)
            elif command_history['active-command'] == "/addalarm":
                self.add_alarm(chat_id=chat_id, command_history=command_history)
            elif command_history['active-command'] == "/delalarm":
                self.del_alarm(chat_id=chat_id, command_history=command_history)
            else:
                self.send_message(prepared_data={"chat_id": chat_id,"text": "Sorry, command unknow. type /help to have list of command."})
    
        return response
