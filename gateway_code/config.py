# -*- coding:utf-8 -*-

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


""" Common static configuration for the application  """

import stat
import os
import json

STAT_0666 = (stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP |
             stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)

PKG_DIR = os.path.abspath(os.path.dirname(__file__))
STATIC_DIR = os.path.join(PKG_DIR, 'static')


def static_path(static_file):
    """ Return the 'static_file' relative path """
    return os.path.join(STATIC_DIR, static_file)


GATEWAY_CONFIG_PATH = os.environ.get('IOTLAB_GATEWAY_CFG_DIR',
                                     '/var/local/config/')
GATEWAY_CONFIG_PATH = os.path.abspath(GATEWAY_CONFIG_PATH)

IOTLAB_USERS = os.environ.get('IOTLAB_USERS_DIR', '/iotlab/users')
EXP_FILES_DIR = os.path.join(IOTLAB_USERS, '{user}/.iot-lab/{exp_id}/')
EXP_FILES = {
    'consumption': 'consumption/{node_id}.oml',
    'radio': 'radio/{node_id}.oml',
    'event': 'event/{node_id}.oml',
    'sniffer': 'sniffer/{node_id}.oml',
    'clock': 'clock_{node_id}.oml',
    'log': 'log/{node_id}.log',
}


def create_user_file(file_path, mode='w'):
    """ Creat a file that can be read and modified by user """
    open(file_path, mode).close()
    os.chmod(file_path, STAT_0666)
    return file_path


def clean_user_file(file_path):
    """ Clean a user file if empty """
    try:
        if os.path.getsize(file_path) == 0:
            os.remove(file_path)
    except OSError:
        pass


DEFAULT_PROFILE = json.load(open(static_path('default_profile.json')))


def read_config(key, default=IOError):
    """ Read 'key' from config. If 'key' is not present raise an IOError
    if 'default' is not provided.

    :param key: Return configuration for 'key'
    :param default: return default if provided and 'key' absent
    :raises IOError: when 'key' can't be read and default not provided """

    entry = os.path.join(GATEWAY_CONFIG_PATH, key)

    try:
        with open(entry) as _conf:
            return _conf.read().strip().lower().replace('-', '_')
    except IOError:
        if default is IOError:  # not provided
            raise
        return default
