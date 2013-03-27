#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""

Logger for gateway code

Set 'logfile' path with 'add_rotating_handler'.

Get logger with 'logger()'


"""

import logging
from logging.handlers import RotatingFileHandler

LOGGER = logging.getLogger()

# set default logger level to DEBUG to log everything
LOGGER.setLevel(logging.DEBUG)
FORMATTER = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')



def add_rotating_handler(logfile, log_level=logging.DEBUG):
    """
    Add a rotating file handler size 1Mo in append mode, with one backup

    :param logfile: path of the log
    :param level: debug level for the handler (default logging.DEBUG)
    """
    file_handler = RotatingFileHandler(logfile, 'a', \
           maxBytes=1000000, backupCount=1)

    file_handler.setLevel(log_level)
    file_handler.setFormatter(FORMATTER)

    LOGGER.addHandler(file_handler)

def logger():
    """
    :return: the logger
    """

    return LOGGER


# création d'un second handler qui va rediriger chaque écriture de log
# sur la console
#stream_handler = logging.StreamHandler()
#stream_handler.setLevel(logging.DEBUG)
#LOGGER.addHandler(stream_handler)

# Après 3 heures, on peut enfin logguer
# Il est temps de spammer votre code avec des logs partout :
#LOGGER.info('Hello')
#LOGGER.warning('Testing %s', 'foo')

