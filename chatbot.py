# coding=UTF-8

from bottle import Bottle, response, request as bottle_request
from telegram import BotHandlerMixin
from copy import deepcopy

import inspect

HELP = {
    "/help":"Display this message",
    "/welcome":"Display the Welcome message",
    "/addfav":"add a favory",
    "/delfav":"remove a favory",
    "/showfav":"display list of favory",
    "/addalarm":"add an alarm",
    "/delalarm":"remove an alarm",
    "/showalarm":"display list of alarm",
    "/next":"Get the next 5 passages of a specific favory"
}

DEFAULT_DOCUMENT = {
    'user-info':'',
    'favory':{},
    'alarm':[]
}

DEFAULT_HISTORY = {
    'active':None,
    'step':0,
    'history':{
        'message_id':[]
    }
}

def welcome_message(name):
    return "Hi {} !\
        \nI'm Tissegram and I will help you to not miss your bus. \
        \nTo do this, We will create one or more alarms depending of your needs. \
        \nNext, when your bus will approach from you, I will let know know. \
        \n \
        \nFirst, use command /addfav to ad at least one favory.\
        \nNext, use command /addalarm to add a specific alarm. \
        \n \
        \nFinally, to have the full list of command, use /help\
        \n \
        \nI really hope you will enjoy the service".format(name)



class Chatbot(BotHandlerMixin, Bottle): 
    def __init__(self, token, webhook_ip, db, transport, *args, **kwargs):
        BotHandlerMixin.__init__(self, token=token, webhook_ip=webhook_ip)
        Bottle.__init__(self)
        self.db = db
        self.transport = transport
        self.chat_id = ""
        self.callback_id = ""
        self.command = {}
        self.favory = {}
        self.alarm = []
        self.route('/', callback=self.post_handler, method="POST")

        self.reset_messages()

    def post_handler(self):
        # Get data from request
        self.set_data(bottle_request.json)

        is_callback = self.is_callback()
        self.chat_id = self.get_chat_id()

        # Check if user is already know and that users data are up to date
        db_doc = self.db.get_document(self.chat_id)
        if db_doc is None:
            new_user = deepcopy(DEFAULT_DOCUMENT)
            new_user['user-info'] = self.get_user_info()
            self.db.insert(user_id=self.chat_id, document=new_user)
            self.welcome()
            return response

        # In case we need to update user-info
        elif db_doc['user-info'] != self.get_user_info():
            self.db.insert(user_id=self.chat_id, document={'user-info':self.get_user_info()})

        # Get var command from database
        self.favory = self.db.get_document(user_id=self.chat_id)['favory']
        self.alarm = self.db.get_document(user_id=self.chat_id)['alarm']

        # Get command history from RAM
        if not self.chat_id in self.command.keys():
            self.command[self.chat_id] = deepcopy(DEFAULT_HISTORY)

        if not is_callback:
            # Get message
            message = self.get_message()
            message_id = self.get_message_id()

            # If message is a command, clear history
            if message[0] == '/':
                try:
                    self.__delete_messages()
                    del self.command[self.chat_id]
                    self.command[self.chat_id] = deepcopy(DEFAULT_HISTORY)
                except KeyError:
                    pass

                # Call method name
                try:
                    getattr(self, message[1:])() # Don't get the '/'
                except AttributeError: # Command is not implemented
                    self.not_implemented()

            elif self.command[self.chat_id]['active'] is None:
                self.not_implemented()

            else:
                getattr(self, self.command[self.chat_id]['active'])(callback=message, message_id=message_id) # Don't get the '/'

        else:
            # Get callback
            callback = self.get_callback()

            # Get callback id
            self.callback_id = self.get_callback_id()

            # Call method name
            getattr(self, self.command[self.chat_id]['active'])(callback=callback)
    
        return response

    def not_implemented(self):
        message = "Sorry, this command is not implemented.\
            \nPlease use command /help to obtain list of command."

        self.send_message(chat_id=self.chat_id, message=message)

    def help(self):
        message = ""
        for key, value in HELP.items():
            message += "{}\n          -> {}\n".format(key, value)

        self.send_message(chat_id=self.chat_id, message=message)

    def welcome(self):
        message = welcome_message(self.get_user_name())

        self.send_message(chat_id=self.chat_id, message=message)

    def addfav(self, callback=None, message_id=None):
        if self.command[self.chat_id]['step'] == 0:
            self.command[self.chat_id]['step'] += 1
            self.command[self.chat_id]['active'] = inspect.stack()[0][3]

            message = "Ok, we will add a new favory together.\
                \nFirst, tell me approximately the name of the stop area"
            return_id = self.send_message(chat_id=self.chat_id, message=message)
            self.command[self.chat_id]['history']['message_id'].append(return_id)


        elif self.command[self.chat_id]['step'] == 1:
            self.command[self.chat_id]['history']['message_id'].append(message_id)
            places = self.transport.get_places(term=callback)
            if len(places) > 0:
                message = "Well. Now, selected the correct area in the list below:\n"
                user_callback = {"inline_keyboard":[]}
                for place in places:
                    user_callback["inline_keyboard"].append([{"text":place[1], "callback_data":place[0]}])

                return_id = self.send_callback(chat_id=self.chat_id, message=message, callback=user_callback)
                self.command[self.chat_id]['history']['message_id'].append(return_id)
                self.command[self.chat_id]['step'] += 1
            
            else:
                message = "Sorry, no input matches with your request. Can you try again:"
                return_id = self.send_message(chat_id=self.chat_id, message=message)
                self.command[self.chat_id]['history']['message_id'].append(return_id)

            
        elif self.command[self.chat_id]['step'] == 2:
            self.answer_callback(callback_id=self.callback_id)

            lines = self.transport.get_lines_by_stoppoints(stopId=callback)
            if len(lines) > 0:
                message = "Select the line:\n"
                user_callback = {"inline_keyboard":[]}
                text = ""
                i = 0
                self.command[self.chat_id]['history']["line-selection"] = []
                for line in lines:
                    text = "line {} direction {}".format(line['line-name'], line['dest-name'])
                    user_callback["inline_keyboard"].append([{"text":text, "callback_data":str(i)}])
                    line['stop-id'] = callback
                    self.command[self.chat_id]['history']["line-selection"].append(dict(line))
                    i += 1

                return_id = self.send_callback(chat_id=self.chat_id, message=message, callback=user_callback)
                self.command[self.chat_id]['history']['message_id'].append(return_id)
                self.command[self.chat_id]['step'] += 1
            
            else:
                message = "Sorry, there are no lines for this area..."
                self.send_message(chat_id=self.chat_id, message=message)
                del self.command[self.chat_id]


        elif self.command[self.chat_id]['step'] == 3:
            self.answer_callback(callback_id=self.callback_id)

            self.command[self.chat_id]['history']["line-selected"] = self.command[self.chat_id]['history']["line-selection"][int(callback)]
            message = "Finaly, give a name for your favory:"

            return_id = self.send_message(chat_id=self.chat_id, message=message)
            self.command[self.chat_id]['history']['message_id'].append(return_id)
            self.command[self.chat_id]['step'] += 1


        elif self.command[self.chat_id]['step'] == 4:
            self.command[self.chat_id]['history']['message_id'].append(message_id)
            if callback not in self.favory.keys():
                self.favory[callback] = self.command[self.chat_id]['history']["line-selected"]
                self.__write_favory()
                message = "Congratulation, your favory {} is succesfully saved !".format(callback)
                self.send_message(chat_id=self.chat_id, message=message)
                self.__delete_messages()
                del self.command[self.chat_id]

            else:
                message = "Name {} is already used. Please select another name:".format(callback)
                return_id = self.send_message(chat_id=self.chat_id, message=message)
                self.command[self.chat_id]['history']['message_id'].append(return_id)

    def delfav(self, callback=None, message_id=None):
        if self.command[self.chat_id]['step'] == 0:
            self.command[self.chat_id]['active'] = inspect.stack()[0][3]

            if len(self.favory) > 0:
                message = "Select the favory you wanna delete:"
                user_callback = {"inline_keyboard":[]}
                for key, value in self.favory.items():
                    text = "\n{} -> line {} destination {}".format(key, value['line-name'], value['dest-name'])
                    user_callback["inline_keyboard"].append([{"text":text, "callback_data":key}])

                return_id = self.send_callback(chat_id=self.chat_id, message=message, callback=user_callback)
                self.command[self.chat_id]['history']['message_id'].append(return_id)
                self.command[self.chat_id]['step'] += 1
            else:
                self.command[self.chat_id]['active'] = None
                self.command[self.chat_id]['history'].clear()
                message = "You don't have any favory for now."
                return_id = self.send_message(chat_id=self.chat_id, message=message)
                self.command[self.chat_id]['history']['message_id'].append(return_id)

        elif self.command[self.chat_id]['step'] == 1:
            self.answer_callback(callback_id=self.callback_id)
            self.__delete_messages()
            del self.command[self.chat_id]
            
            del self.favory[callback]
            self.__write_favory()
            message = "Congratulation, your favory {} is succesfully deleted !".format(callback)
            self.send_message(chat_id=self.chat_id, message=message)

    def showfav(self):
        message = ""
        if len(self.favory) > 0:
            message += "Here is your favories :"
            for key, value in self.favory.items():
                message += "\n{} -> line {} destination {}".format(key, value['line-name'], value['dest-name'])
        
        else:
            message += "Sorry, your favory list is empty for now.\
                \nPlease use /addfav command to add a new one."

        self.send_message(chat_id=self.chat_id, message=message)

    def addalarm(self, callback=None, message_id=None):
        if self.command[self.chat_id]['step'] == 0:
            self.command[self.chat_id]['active'] = inspect.stack()[0][3]

            if len(self.favory) > 0:
                message = "Select the favory you wanna add an alarm:"
                user_callback = {"inline_keyboard":[]}
                for key, value in self.favory.items():
                    text = "\n{} -> line {} destination {}".format(key, value['line-name'], value['dest-name'])
                    user_callback["inline_keyboard"].append([{"text":text, "callback_data":key}])

                return_id = self.send_callback(chat_id=self.chat_id, message=message, callback=user_callback)
                self.command[self.chat_id]['history']['message_id'].append(return_id)
                self.command[self.chat_id]['step'] += 1
            else:
                message = "You don't have any favory for now. Use /addfav to add one"
                self.send_message(chat_id=self.chat_id, message=message)
                del self.command[self.chat_id]

        elif self.command[self.chat_id]['step'] == 1:
            self.answer_callback(callback_id=self.callback_id)

            self.command[self.chat_id]['history']['favory'] = callback

            message = "Tell me the approximate hour for this line (ex: 8h30 or 8h..):"
            return_id = self.send_message(chat_id=self.chat_id, message=message)
            self.command[self.chat_id]['history']['message_id'].append(return_id)
            self.command[self.chat_id]['step'] += 1

        elif self.command[self.chat_id]['step'] == 2:
            correct_format = True
            date = callback.split('h')
            if len(date) < 2:
                correct_format = False

            elif len(date) == 2:
                try:
                    hour = int(date[0])
                    if date[1] != '':
                        minute = int(date[1])
                    else:
                        minute = 0
                except:
                    correct_format = False

            else:
                correct_format = False

            if correct_format:
                if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                    correct_format = False

            if correct_format is False:
                message = "Sorry, your date format is not correct. Try again :(ex: 8h30 or 8h..)"
                self.send_message(chat_id=self.chat_id, message=message)

            else:
                list_passage = self.transport.get_passages( dest_id=self.favory[self.command[self.chat_id]['history']['favory']]['dest-id'],
                                                            stop_id=self.favory[self.command[self.chat_id]['history']['favory']]['stop-id'],
                                                            line_id=self.favory[self.command[self.chat_id]['history']['favory']]['line-id'],
                                                            hour=hour,
                                                            minute=minute)

                if len(list_passage) > 0:
                    message = "Select the best date:"
                    user_callback = {"inline_keyboard":[]}
                    i = 0
                    self.command[self.chat_id]['history']["selection"] = []
                    for passage in list_passage:
                        text = "{}".format(passage['date'])
                        user_callback["inline_keyboard"].append([{"text":text, "callback_data":str(i)}])
                        self.command[self.chat_id]['history']["selection"].append(dict(passage))
                        i += 1

                    return_id = self.send_callback(chat_id=self.chat_id, message=message, callback=user_callback)
                    self.command[self.chat_id]['history']['message_id'].append(return_id)
                    self.command[self.chat_id]['step'] += 1
                else:
                    message = "Sorry, No passages.."
                    self.send_message(chat_id=self.chat_id, message=message)
                    del self.command[self.chat_id]

        elif self.command[self.chat_id]['step'] == 3:
            self.answer_callback(callback_id=self.callback_id)
            self.command[self.chat_id]['history']["selection"][int(callback)]['favory'] = self.command[self.chat_id]['history']['favory']
            self.alarm.append(self.command[self.chat_id]['history']["selection"][int(callback)])
            self.__write_alarm()
            message = "Congratulation, your alarm is succesfully saved !"
            self.send_message(chat_id=self.chat_id, message=message)
            self.__delete_messages()
            del self.command[self.chat_id]

    def delalarm(self, callback=None, message_id=None):
        if self.command[self.chat_id]['step'] == 0:
            self.command[self.chat_id]['active'] = inspect.stack()[0][3]

            if len(self.alarm) > 0:
                message = "Select the alarm you wanna delete:"
                user_callback = {"inline_keyboard":[]}
                for i in range(0, len(self.alarm)):
                    text = "\nFavory name :{} -> at {}".format(self.alarm[i]['favory'], self.alarm[i]['date'])
                    user_callback["inline_keyboard"].append([{"text":text, "callback_data":i}])

                return_id = self.send_callback(chat_id=self.chat_id, message=message, callback=user_callback)
                self.command[self.chat_id]['history']['message_id'].append(return_id)
                self.command[self.chat_id]['step'] += 1
            else:
                message = "You don't have any alarm for now."
                self.send_message(chat_id=self.chat_id, message=message)
                del self.command[self.chat_id]

        elif self.command[self.chat_id]['step'] == 1:
            self.answer_callback(callback_id=self.callback_id)
            self.__delete_messages()
            del self.command[self.chat_id]
            
            self.alarm.pop(int(callback))
            self.__write_alarm()
            message = "Congratulation, your alarm is succesfully deleted !"
            self.send_message(chat_id=self.chat_id, message=message)
     
    def showalarm(self):
        message = ""
        if len(self.alarm) > 0:
            message += "Here is your alarms :"
            for alarm in self.alarm:
                message += "\nFavory name :{} -> at {}".format(alarm['favory'], alarm['date'])
        
        else:
            message += "Sorry, your alarm list is empty for now.\
                \nPlease use /addalarm command to add a new one."

        self.send_message(chat_id=self.chat_id, message=message)

    def next(self, callback=None, message_id=None):
        if self.command[self.chat_id]['step'] == 0:
            self.command[self.chat_id]['active'] = inspect.stack()[0][3]

            if len(self.favory) > 0:
                message = "Select the favory you wanna know the next passages:"
                user_callback = {"inline_keyboard":[]}
                for key, value in self.favory.items():
                    text = "\n{} -> line {} destination {}".format(key, value['line-name'], value['dest-name'])
                    user_callback["inline_keyboard"].append([{"text":text, "callback_data":key}])

                self.send_callback(chat_id=self.chat_id, message=message, callback=user_callback)
                self.command[self.chat_id]['step'] += 1
            else:
                message = "You don't have any favory for now. Use /addfav to add one"
                self.send_message(chat_id=self.chat_id, message=message)
                del self.command[self.chat_id]

        elif self.command[self.chat_id]['step'] == 1:
            self.answer_callback(callback_id=self.callback_id)

            message = ""
            list_next_passages = self.transport.get_next_passages(  line=self.favory[callback]['line-name'],
                                                                    dest_id=self.favory[callback]['dest-id'],
                                                                    stop_id=self.favory[callback]['stop-id'],
                                                                    line_id=self.favory[callback]['line-id'])
            if len(list_next_passages) > 0:
                message += "Next {} passages for this line:\n".format(len(list_next_passages))
                for next in list_next_passages:
                    message += "\n{} -> in {} minutes".format(next[0], next[1])

            else:
                message += "Sorry, there is no passages for now."

            self.send_message(chat_id=self.chat_id, message=message)
            del self.command[self.chat_id]

    def __write_favory(self):
        self.db.insert(user_id=self.chat_id, document={'favory':self.favory})

    def __write_alarm(self):
        self.db.insert(user_id=self.chat_id, document={'alarm':self.alarm})

    def __delete_messages(self):
        self.delete_message(chat_id=self.chat_id, message_id=self.command[self.chat_id]['history']['message_id'])