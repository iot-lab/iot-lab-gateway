#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Logger for gateway code

Set 'logfile' path with 'add_rotating_handler'.
"""

import logging
from logging.handlers import RotatingFileHandler



# set default logger level to DEBUG to log everything
LOGLEVEL = logging.DEBUG
FORMATTER = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')

def init_logger(log_folder):
    """
    Create global logger and handlers

    :param log_folder: destination folder for the logs
    """

    log_folder += '/'

    logger = logging.getLogger('gateway_code')
    logger.setLevel(LOGLEVEL)

    # user logs
    # will be updated to be in user folder later
    user_f = log_folder + 'user.log'
    user = RotatingFileHandler(user_f, 'a', maxBytes=100000, backupCount=1)
    user.setLevel(logging.ERROR)
    user.setFormatter(FORMATTER)

    # Server logs
    server_f = log_folder + 'gateway-server.log'
    server = RotatingFileHandler(server_f, 'a', maxBytes=1000000, backupCount=1)
    server.setLevel(logging.DEBUG)
    server.setFormatter(FORMATTER)


    # add handlers
    logger.addHandler(server)
    logger.addHandler(user)
