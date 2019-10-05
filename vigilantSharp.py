#!/usr/bin/python3
# coding=UTF-8

import configparser
import argparse


def main(args):
    config = configparser.ConfigParser()
    config.read('conf.ini')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description = "Telegram Bot",
        fromfile_prefix_chars = '@' )
    parser.add_argument(
        "-v",
        "--verbose",
        help="verbose mode",
        required = False,
        action="store_true")
    args = parser.parse_args()
    main(args)