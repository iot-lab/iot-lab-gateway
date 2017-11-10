# -*- coding: utf-8 -*-

# This file is a part of IoT-LAB gateway_code
# Copyright (C) 2015 INRIA (Contact: admin@iot-lab.info)
# Contributor(s) : see AUTHORS file
#
# This software is governed by the CeCILL license under French law
# and abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# http://www.cecill.info.
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.


"""
Logger configuration for gateway code
"""

import sys
import logging
from logging.handlers import RotatingFileHandler

# set default logger level to DEBUG to log everything
LOGLEVEL = logging.DEBUG
FORMATTER = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')

LOGGER = logging.getLogger('gateway_code')


def init_logger(log_folder, log_stdout=False):
    """ Create global logger and handlers

    :param log_folder: log destination folder
    :param log_stdout: whether to log everything to stdout
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

    # stdout log (useful for dockerized)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(FORMATTER)

    # add handlers
    logger.addHandler(server)
    if log_stdout:
        logger.addHandler(ch)


def user_logger(log_file_path):
    """ Create a logger for user logs in `log_file_path` """
    user_log = logging.FileHandler(log_file_path)
    user_log.setLevel(logging.INFO)
    user_log.setFormatter(FORMATTER)
    return user_log
