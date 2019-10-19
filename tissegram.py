#!/usr/bin/python3
# coding=UTF-8

from database import DataBase
from chatbot import Chatbot
from public_transport import PublicTransport
from log import get_logger

import configparser
import argparse
import time
import threading


def main(args):
    # Configure Logger
    level = 'NOTSET'
    if args.verbose:
        level = 'DEBUG'
    logger = get_logger(name="main",level=level)
    logger.info("Starting Tissegram")

    # Get Config
    logger.info("Get Config")
    config = configparser.ConfigParser()
    config.read(args.conf)

    logger.info("Init database module")
    db = DataBase(  ip=config['Database']['ip'],
                    port=config['Database']['port'],
                    database=config['Database']['database'],
                    username=config['Database']['username'],
                    password=config['Database']['password'])

    logger.info("Init transport module")
    transport = PublicTransport(token=config['Tisseo']['token'])

    logger.info("Init bot module")
    bot = Chatbot(token=config['Telegram']['token'], webhook_ip=config['Telegram']['webhook'], db=db, transport=transport)

    logger.info("Start thread")
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