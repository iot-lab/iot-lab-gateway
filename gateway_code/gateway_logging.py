# -*- coding: utf-8 -*-

"""
Logger configuration for gateway code
"""

import logging
from logging.handlers import RotatingFileHandler

# set default logger level to DEBUG to log everything
LOGLEVEL = logging.DEBUG
FORMATTER = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')

LOGGER = logging.getLogger('gateway_code')


def init_logger(log_folder):
    """ Create global logger and handlers

    :param log_folder: log destination folder
    """

    logger = LOGGER
    logger.setLevel(LOGLEVEL)

    if logger.handlers != []:
        return

    # Server logs
    server_f = log_folder + '/' + 'gateway-server.log'
    server = RotatingFileHandler(
        server_f, 'a', maxBytes=1000000, backupCount=1)
    server.setLevel(logging.DEBUG)
    server.setFormatter(FORMATTER)

    # add handlers
    logger.addHandler(server)


def user_logger(log_file_path):
    """ Create a logger for user logs in `log_file_path` """
    user_log = logging.FileHandler(log_file_path)
    user_log.setLevel(logging.INFO)
    user_log.setFormatter(FORMATTER)
    return user_log
