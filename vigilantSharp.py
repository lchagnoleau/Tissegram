#!/usr/bin/python3
# coding=UTF-8

from database import DataBase
from chatbot import Chatbot

import configparser
import argparse


def main(args):
    config = configparser.ConfigParser()
    config.read(args.conf)

    db = DataBase(  ip=config['Database']['ip'],
                    port=config['Database']['port'],
                    database=config['Database']['database'],
                    username=config['Database']['username'],
                    password=config['Database']['password'])

    # test database
    #db.insert(chat_id='0123456', document={'test3':15})

    bot = Chatbot(token=config['Telegram']['token'])
    # bot.send_message({"chat_id": 0123456,"text": "coucou"})

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description = "Telegram Bot",
        fromfile_prefix_chars = '@' )
    parser.add_argument(
        "-v",
        "--verbose",
        help="verbose mode",
        required = False,
        action="store_true"),
    parser.add_argument(
        "-c",
        "--conf",
        help="Path to conf",
        required = True)
    args = parser.parse_args()
    main(args)