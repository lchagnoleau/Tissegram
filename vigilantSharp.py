#!/usr/bin/python3
# coding=UTF-8

from database import DataBase
from chatbot import Chatbot
from public_transport import PublicTransport

import configparser
import argparse
import time
import threading


def main(args):
    config = configparser.ConfigParser()
    config.read(args.conf)

    db = DataBase(  ip=config['Database']['ip'],
                    port=config['Database']['port'],
                    database=config['Database']['database'],
                    username=config['Database']['username'],
                    password=config['Database']['password'])

    transport = PublicTransport(token=config['Tisseo']['token'])

    # print(transport.get_line(line="79"))
    # print(transport.get_points(line_id="11821949021891674"))

    bot = Chatbot(token=config['Telegram']['token'], db=db, transport=transport)
    threading.Thread(target=bot.run, kwargs=dict(host='localhost', port=5001)).start()

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