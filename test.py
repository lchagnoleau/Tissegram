# coding=UTF-8

import copy

DEFAULT_DICT = {
    'history':{
        'id':[]
    }
}

my_dict = copy.deepcopy(DEFAULT_DICT)
print("my_dict is {}".format(my_dict))
print("DEFAULT_DICT is {}".format(DEFAULT_DICT))

my_dict['history']['id'].append("toto")
print("my_dict is {}".format(my_dict))
print("DEFAULT_DICT is {}".format(DEFAULT_DICT))