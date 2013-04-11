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

LOG_FOLDER = "/var/log/gateway-server/"



LOGGER = logging.getLogger("gateway_logger")
LOGGER.setLevel(LOGLEVEL)

FORMATTER = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')





# Server logs
LOGFILE = LOG_FOLDER + "gateway-server.log"
FILE = RotatingFileHandler(LOGFILE, 'a', maxBytes=1000000, backupCount=1)

FILE.setLevel = logging.DEBUG
FILE.setFormatter(FORMATTER)
LOGGER.addHandler(FILE)

LOGFILE_USER = LOG_FOLDER + "user.log"
USER_FILE = RotatingFileHandler(LOGFILE_USER, 'a',\
        maxBytes=100000, backupCount=1)
USER_FILE.setLevel = logging.ERROR
USER_FILE.setFormatter(FORMATTER)
LOGGER.addHandler(USER_FILE)



# console handler
# STREAM_HANDLER = logging.StreamHandler()
# STREAM_HANDLER.setLevel(logging.DEBUG)

# LOGGER.addHandler(STREAM_HANDLER)


#LOGGER.info('Hello')
#LOGGER.warning('Testing %s', 'foo')
