# coding=UTF-8

import logging.config
from os import path, makedirs

handlers = ['file']

class log(logging.Logger):
    def __init__(self, name, level=logging.DEBUG):
        logging.Logger.__init__(self, name, level)

    def info(self, msg, *args, **kwargs):
        logging.Logger.info(self, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        logging.Logger.warning(self, msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        logging.Logger.debug(self, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        logging.Logger.error(self, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        logging.Logger.critical(self, msg, *args, **kwargs)

def get_logger(name, log_path="/var/log/tissegram/", level=None):
    global handlers
    if not path.exists(log_path):
        makedirs(log_path)
    if level is not None:
        if level != "NOTSET":
            handlers = ['default', 'file']
    logging.setLoggerClass(log)
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format':  '%(asctime)s [%(levelname)s] %(name)s : %(message)s',
                'datefmt': '%a %d %H:%M:%S'
                },
            'simple': {
                'format': '%(levelname)s %(message)s'
                },
            'customFormat': {
                '()' : 'colorlog.ColoredFormatter',
                'format':  '%(asctime)s [%(levelname)s] %(name)s : %(message_log_color)s%(message)s',
                'datefmt': '%a %d %H:%M:%S',
                'secondary_log_colors' : {
                    'message': {
                        'INFO':     'green',
                        'DEBUG':    'blue',
                        'WARNING':  'yellow',
                        'ERROR':    'red',
                        'CRITICAL': 'red'
                        }
                    }
                }
            },
        'handlers': {
            'default': {
                'level':level,
                'class':'logging.StreamHandler',
                'formatter': 'customFormat'
            },
            'file': {
                'level': 'DEBUG',
                'formatter': 'customFormat',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': log_path + 'all.log',
                'encoding': 'utf8',
                'maxBytes': 100000000,
                'backupCount': 3
            }
        },
        'loggers': {
            '': {
                'propagate' : True,
                'handlers': handlers,
                'level': 'DEBUG'
            }
        }
    })
    return logging.getLogger(name)