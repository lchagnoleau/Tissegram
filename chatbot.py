# coding=UTF-8

from bottle import Bottle, response, request as bottle_request
from telegram import BotHandlerMixin
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
    'alarm':{},
    'command':{
        'active':None,
        'step':0,
        'history':{}
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
    def __init__(self, token, db, transport, *args, **kwargs):
        BotHandlerMixin.__init__(self, token=token)
        Bottle.__init__(self)
        self.db = db
        self.transport = transport
        self.chat_id = ""
        self.callback_id = ""
        self.command = {}
        self.favory = {}
        self.alarm = []
        self.route('/', callback=self.post_handler, method="POST")

    def post_handler(self):
        # Get data from request
        self.set_data(bottle_request.json)

        is_callback = self.is_callback()
        self.chat_id = self.get_chat_id()

        # Check if user is already know and that users data are up to date
        db_doc = self.db.get_document(self.chat_id)
        if db_doc is None:
            new_user = dict(DEFAULT_DOCUMENT)
            new_user['user-info'] = self.get_user_info()
            self.db.insert(user_id=self.chat_id, document=new_user)
            self.welcome()
            return response

        # In case we need to update user-info
        elif db_doc['user-info'] != self.get_user_info():
            self.db.insert(user_id=self.chat_id, document={'user-info':self.get_user_info()})

        # Get var command from database
        self.command = self.db.get_document(user_id=self.chat_id)['command']
        self.favory = self.db.get_document(user_id=self.chat_id)['favory']
        self.alarm = self.db.get_document(user_id=self.chat_id)['alarm']

        if not is_callback:
            # Get message
            message = self.get_message()

            # If message is a command, clear history
            if message[0] == '/':
                self.__clear_command()

                # Call method name
                try:
                    getattr(self, message[1:])() # Don't get the '/'
                except: # Command is not implemented
                    self.not_implemented()

            elif self.command['active'] is None:
                self.not_implemented()

            else:
                getattr(self, self.command['active'])(callback=message) # Don't get the '/'

        else:
            # Get callback
            callback = self.get_callback()

            # Get callback id
            self.callback_id = self.get_callback_id()

            # Call method name
            getattr(self, self.command['active'])(callback=callback)
    
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

    def test(self, callback=None):
        if self.command['step'] == 0:
            self.command['step'] += 1
            self.command['active'] = inspect.stack()[0][3]

            message = "Tell me something :"
            self.send_message(chat_id=self.chat_id, message=message)

        elif self.command['step'] == 1:
            self.command['step'] = 0
            self.command['active'] = None
            self.command['history'].clear()

            message = "Ok, you send me : " + callback
            self.send_message(chat_id=self.chat_id, message=message)

        self.__write_command()

    def addfav(self, callback=None):
        if self.command['step'] == 0:
            self.command['step'] += 1
            self.command['active'] = inspect.stack()[0][3]

            message = "Ok, we will add a new favory together.\
                \nFirst, tell me approximately the name of the stop area"
            self.send_message(chat_id=self.chat_id, message=message)


        elif self.command['step'] == 1:
            places = self.transport.get_places(term=callback)
            if len(places) > 0:
                message = "Well. Now, selected the correct area in the list below:\n"
                user_callback = {"inline_keyboard":[]}
                for place in places:
                    user_callback["inline_keyboard"].append([{"text":place[1], "callback_data":place[0]}])

                self.send_callback(chat_id=self.chat_id, message=message, callback=user_callback)
                self.command['step'] += 1
            
            else:
                message = "Sorry, no input matches with your request. Can you try again:"
                self.send_message(chat_id=self.chat_id, message=message)

            
        elif self.command['step'] == 2:
            self.answer_callback(callback_id=self.callback_id)

            lines = self.transport.get_lines_by_stoppoints(stopId=callback)
            if len(lines) > 0:
                message = "Select the line:\n"
                user_callback = {"inline_keyboard":[]}
                text = ""
                i = 0
                self.command['history']["line-selection"] = []
                for line in lines:
                    text = "line {} direction {}".format(line['line-name'], line['dest-name'])
                    user_callback["inline_keyboard"].append([{"text":text, "callback_data":str(i)}])
                    line['stop-id'] = callback
                    self.command['history']["line-selection"].append(dict(line))
                    i += 1

                self.send_callback(chat_id=self.chat_id, message=message, callback=user_callback)
                self.command['step'] += 1
            
            else:
                self.command['step'] = 0
                self.command['active'] = None
                self.command['history'].clear()
                message = "Sorry, there are no lines for this area..."
                self.send_message(chat_id=self.chat_id, message=message)


        elif self.command['step'] == 3:
            self.answer_callback(callback_id=self.callback_id)

            self.command['history']["line-selected"] = self.command['history']["line-selection"][int(callback)]
            message = "Finaly, give a name for your favory:"

            self.send_message(chat_id=self.chat_id, message=message)
            self.command['step'] += 1


        elif self.command['step'] == 4:
            if callback not in self.favory.keys():
                self.favory[callback] = self.command['history']["line-selected"]
                self.__write_favory()
                message = "Congratulation, your favory {} is succesfully saved !".format(callback)
                self.command['step'] = 0
                self.command['active'] = None
                self.command['history'].clear()

            else:
                message = "Name {} is already used. Please select another name:".format(callback)

            self.send_message(chat_id=self.chat_id, message=message)


        self.__write_command()


    def delfav(self, callback=None):
        if self.command['step'] == 0:
            self.command['active'] = inspect.stack()[0][3]

            if len(self.favory) > 0:
                message = "Select the favory you wanna delete:"
                user_callback = {"inline_keyboard":[]}
                for key, value in self.favory.items():
                    text = "\n{} -> line {} destination {}".format(key, value['line-name'], value['dest-name'])
                    user_callback["inline_keyboard"].append([{"text":text, "callback_data":key}])

                self.send_callback(chat_id=self.chat_id, message=message, callback=user_callback)
                self.command['step'] += 1
            else:
                self.command['active'] = None
                self.command['history'].clear()
                message = "You don't have any favory for now."
                self.send_message(chat_id=self.chat_id, message=message)

        elif self.command['step'] == 1:
            self.answer_callback(callback_id=self.callback_id)

            self.command['step'] = 0
            self.command['active'] = None
            self.command['history'].clear()
            
            del self.favory[callback]
            self.__write_favory()
            message = "Congratulation, your favory {} is succesfully deleted !".format(callback)
            self.send_message(chat_id=self.chat_id, message=message)
     
        self.__write_command()

    def showfav(self):
        message = ""
        if len(self.favory) > 0:
            message += "Here is your favories :"
            for key, value in self.favory.items():
                print(key)
                print(value)
                message += "\n{} -> line {} destination {}".format(key, value['line-name'], value['dest-name'])
        
        else:
            message += "Sorry, your favory list is empty for now.\
                \nPlease use /addfav command to add a new one."

        self.send_message(chat_id=self.chat_id, message=message)

    def addalarm(self, callback=None):
        pass

    def delalarm(self, callback=None):
        if self.command['step'] == 0:
            self.command['active'] = inspect.stack()[0][3]

            if len(self.alarm) > 0:
                message = "Select the alarm you wanna delete:"
                user_callback = {"inline_keyboard":[]}
                for i in len(0, self.alarm):
                    day = ""
                    for d in self.alarm[i]['day']:
                        day += "{},".format(d)
                    day = day[:-1]
                    text = "\nFavory name :{} -> {} at {}".format(self.alarm[i]['line'], day, self.alarm[i]['time'])
                    user_callback["inline_keyboard"].append([{"text":text, "callback_data":i}])

                self.send_callback(chat_id=self.chat_id, message=message, callback=user_callback)
                self.command['step'] += 1
            else:
                self.command['active'] = None
                self.command['history'].clear()
                message = "You don't have any alarm for now."
                self.send_message(chat_id=self.chat_id, message=message)

        elif self.command['step'] == 1:
            self.answer_callback(callback_id=self.callback_id)

            self.command['step'] = 0
            self.command['active'] = None
            self.command['history'].clear()
            
            self.alarm.pop(callback)
            self.__write_favory()
            message = "Congratulation, your alarm is succesfully deleted !"
            self.send_message(chat_id=self.chat_id, message=message)
     
        self.__write_command()
    def showalarm(self):
        message = ""
        if len(self.alarm) > 0:
            message += "Here is your alarms :"
            for alarm in self.alarm:
                day = ""
                for d in alarm['day']:
                    day += "{},".format(d)
                day = day[:-1]
                message += "\nFavory name :{} -> {} at {}".format(alarm['line'], day, alarm['time'])
        
        else:
            message += "Sorry, your alarm list is empty for now.\
                \nPlease use /addalarm command to add a new one."

        self.send_message(chat_id=self.chat_id, message=message)

    def next(self, callback=None):
        if self.command['step'] == 0:
            self.command['active'] = inspect.stack()[0][3]

            if len(self.favory) > 0:
                message = "Select the favory you wanna know the next passages:"
                user_callback = {"inline_keyboard":[]}
                for key, value in self.favory.items():
                    text = "\n{} -> line {} destination {}".format(key, value['line-name'], value['dest-name'])
                    user_callback["inline_keyboard"].append([{"text":text, "callback_data":key}])

                self.send_callback(chat_id=self.chat_id, message=message, callback=user_callback)
                self.command['step'] += 1
            else:
                message = "You don't have any favory for now. Use /addfav to add one"
                self.send_message(chat_id=self.chat_id, message=message)

                self.command['step'] = 0
                self.command['active'] = None
                self.command['history'].clear()

        elif self.command['step'] == 1:
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
            self.command['step'] = 0
            self.command['active'] = None
            self.command['history'].clear()

        self.__write_command()

    def __clear_command(self):
        self.db.insert(user_id=self.chat_id, document={'command':{'active':'None', 'step':0, 'history':{}}})

    def __write_command(self):
        self.db.insert(user_id=self.chat_id, document={'command':self.command})

    def __write_favory(self):
        self.db.insert(user_id=self.chat_id, document={'favory':self.favory})