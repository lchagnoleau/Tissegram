# coding=UTF-8

from bottle import Bottle, response, request as bottle_request
from telegram import BotHandlerMixin

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
        'active':'',
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
        self.route('/', callback=self.post_handler, method="POST")

    def post_handler(self):
        # Get data from request
        self.set_data(bottle_request.json)

        is_callback = self.is_callback()
        self.chat_id = self.get_chat_id()

        if not is_callback:

            # Check if user is already know and that users data are up to date
            db_doc = self.db.get_document(self.chat_id)
            if db_doc is None:
                new_user = dict(DEFAULT_DOCUMENT)
                new_user['user-info'] = self.get_user_info()
                self.db.insert(new_user)
                self.send_message({'chat_id':self.chat_id, 'text':welcome_message(self.get_user_name(data))})
                return response

            # In case we need to update user-info
            elif db_doc['user-info'] != self.get_user_info():
                self.db.insert(user_id=self.chat_id, document={'user-info':self.get_user_info()})

            # Get message
            message = self.get_message()

            # If message is a command, clear history
            if message[0] == '/':
                self.__clear_history()

                # Call method name
                try:
                    getattr(self, message[1:])() # Don't get the '/'
                except: # Command is not implemented
                    self.not_implemented()

            else:
                self.not_implemented()

        else:
            callback = self.get_callback()
            command = self.db.get_document(user_id=self.chat_id)['command']
            getattr(self, command['active'])(callback=callback, command=command)

    
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

    def test(self, callback=None, command=None):
        if command is None: # First call to this method
            active = inspect.stack()[0][3]
            message = "Tell me something :"

        self.db.insert(user_id=self.chat_id, document={'command':{'active-command':active, 'step':step, 'history':history}})



    # def add_favory(self, chat_id, command_history=None, message="", callback_id=""):
    #     if command_history is None:
    #         step = 0
    #         history = {}
    #     else:
    #         step = command_history['step']
    #         history = dict(command_history['history'])

    #     active = "/addfav"

    #     if step == 0:
    #         return_message = "Ok, we will add a new favory together.\
    #             \nFirst, tell me approximately the name of the stop area"

    #         self.send_message(prepared_data={"chat_id": chat_id,"text": return_message})
    #         step += 1

    #     elif step == 1:
    #         places = self.transport.get_places(term=message)
    #         if len(places) > 0:
    #             return_message = "Well. Now, selected the correct area in the list below:\n"
    #             callback = {"inline_keyboard":[]}
    #             for place in places:
    #                 callback["inline_keyboard"].append([{"text":place[1], "callback_data":place[0]}])

    #             self.send_message(prepared_data={"chat_id": chat_id, "reply_markup":callback, "text": return_message})
    #             step += 1
            
    #         else:
    #             return_message = "Sorry, no input matches with your request. Can you try again:"
    #             self.send_message(prepared_data={"chat_id": chat_id, "text": return_message})

    #     elif step == 2:
    #         self.answer_callback(prepared_data={"callback_query_id": callback_id})
    #         lines = self.transport.get_lines_by_stoppoints(stopId=message)
    #         if len(lines) > 0:
    #             return_message = "Select the line:\n"
    #             callback = {"inline_keyboard":[]}
    #             text = ""
    #             i = 0
    #             history["line-selection"] = []
    #             for line in lines:
    #                 text = "line {} direction {}".format(line[0], line[1])
    #                 callback["inline_keyboard"].append([{"text":text, "callback_data":str(i)}])
    #                 history["line-selection"].append(line)
    #                 i += 1

    #             self.send_message(prepared_data={"chat_id": chat_id, "reply_markup":callback, "text": return_message})
    #             step += 1
            
    #         else:
    #             return_message = "Sorry, there are no lines for this area..."
    #             self.send_message(prepared_data={"chat_id": chat_id, "text": return_message})
    #             active = "None"
    #             step = 0

    #     elif step == 3:
    #         self.answer_callback(prepared_data={"callback_query_id": callback_id})
    #         history["line-selected"] = history["line-selection"][int(message)]
    #         self.send_message(prepared_data={"chat_id": chat_id, "text": "Finaly, give a name for your favory:"})
    #         step += 1

    #     elif step == 4:
    #         line = self.db.get_document(user_id = chat_id)["command"]["history"]["line-selected"]
    #         l = {
    #             "line":line[0],
    #             "destination":line[1],
    #             "destination-id":line[2],
    #             "stop-id":line[3]
    #         }
    #         favory = self.db.get_document(user_id = chat_id)["favory"]
    #         if message not in favory.keys():
    #             favory[message] = l
    #             self.db.insert(user_id=chat_id, document={'favory':favory})
    #             self.send_message(prepared_data={"chat_id": chat_id, "text": "Congratulation, your favory {} is succesfully saved !".format(message)})
    #             active = "None"
    #             step = 0
    #             history.clear()

    #         else:
    #             self.send_message(prepared_data={"chat_id": chat_id, "text": "Name {} is already used. Please select another name:".format(message)})


    #     self.db.insert(user_id=chat_id, document={'command':{'active-command':active, 'step':step, 'history':history}})

    # def del_favory(self, chat_id, command_history=None, message="", callback_id=""):
    #     if command_history is None:
    #         step = 0
    #         history = {}
    #     else:
    #         step = command_history['step']
    #         history = dict(command_history['history'])

    #     active = "/delfav"

    #     if step == 0:
    #         fav = self.db.get_document(user_id=chat_id)['favory']
    #         if len(fav) > 0:
    #             message = "Select the favory you wanna delete:"
    #             callback = {"inline_keyboard":[]}
    #             for key, value in fav.items():
    #                 text = "\n{} -> line {} destination {}".format(key, value['line'], value['destination'])
    #                 callback["inline_keyboard"].append([{"text":text, "callback_data":key}])

    #             self.send_message(prepared_data={"chat_id": chat_id, "reply_markup":callback, "text": message})
    #             step += 1
    #         else:
    #             message = "You don't have any favory for now."
    #             self.send_message(prepared_data={"chat_id": chat_id, "text": message})
    #             active = "None"
    #             step = 0
    #             history.clear()

    #     elif step == 1:
    #         self.answer_callback(prepared_data={"callback_query_id": callback_id})
    #         fav = self.db.get_document(user_id=chat_id)['favory']
    #         del fav[message]
    #         self.db.insert(user_id=chat_id, document={'favory':fav})
    #         self.send_message(prepared_data={"chat_id": chat_id, "text": "Congratulation, your favory {} is succesfully deleted !".format(message)})
    #         active = "None"
    #         step = 0
    #         history.clear()
     
    #     self.db.insert(user_id=chat_id, document={'command':{'active-command':active, 'step':step, 'history':history}})

    # def show_favory(self, chat_id):
    #     fav = self.db.get_document(user_id=chat_id)['favory']
    #     message = ""
    #     if len(fav) > 0:
    #         message += "Here is your favories :"
    #         for key, value in fav.items():
    #             message += "\n{} -> line {} destination {}".format(key, value['line'], value['destination'])
        
    #     else:
    #         message += "Sorry, your favory list is empty for now.\
    #             \nPlease use /addfav command to add a new one."

    #     self.send_message(prepared_data={"chat_id": chat_id, "text": message})

    # def add_alarm(self, chat_id, command_history=None, message="", callback_id=""):
    #     pass

    # def del_alarm(self, chat_id, command_history=None, message="", callback_id=""):
    #     pass

    # def show_alarm(self, chat_id):
    #     pass

    # def next(self, chat_id, command_history=None, message="", callback_id=""):
    #     if command_history is None:
    #         step = 0
    #         history = {}
    #     else:
    #         step = command_history['step']
    #         history = dict(command_history['history'])

    #     active = "/next"

    #     if step == 0:
    #         favory = self.db.get_document(user_id=chat_id)['favory']
    #         if len(favory) > 0:
    #             message = "Select the favory you wanna know the next passages:"
    #             callback = {"inline_keyboard":[]}
    #             for key, value in favory.items():
    #                 text = "\n{} -> line {} destination {}".format(key, value['line'], value['destination'])
    #                 callback["inline_keyboard"].append([{"text":text, "callback_data":key}])

    #             self.send_message(prepared_data={"chat_id": chat_id, "reply_markup":callback, "text": message})
    #             step += 1
    #         else:
    #             message = "You don't have any favory for now. Use /addfav to add one"
    #             self.send_message(prepared_data={"chat_id": chat_id, "text": message})
    #             active = "None"
    #             step = 0
    #             history.clear()

    #     elif step == 1:
    #         self.answer_callback(prepared_data={"callback_query_id": callback_id})
    #         favory = self.db.get_document(user_id=chat_id)['favory'][message]

    #         text = ""
    #         list_next_passages = self.transport.get_next_passages(line=favory['line'], dest_id=favory['destination-id'], stop_id=favory['stop-id'])
    #         if len(list_next_passages) > 0:
    #             text += "Next {} passages for this line:\n".format(len(list_next_passages))
    #             for next in list_next_passages:
    #                 text += "\n{} -> in {} minutes".format(next[0], next[1])

    #         else:
    #             text += "Sorry, there is no passages for now."

    #         self.send_message(prepared_data={"chat_id": chat_id, "text": text})
    #         active = "None"
    #         step = 0
    #         history.clear()

    #     self.db.insert(user_id=chat_id, document={'command':{'active-command':active, 'step':step, 'history':history}})

    def __clear_history(self):
        self.db.insert(user_id=self.chat_id, document={'command':{'active-command':'None', 'step':'', 'history':{}}})