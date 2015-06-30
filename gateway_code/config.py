# -*- coding:utf-8 -*-

""" Common static configuration for the application  """

import stat
import os

STAT_0666 = (stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP |
             stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)

PKG_DIR = os.path.abspath(os.path.dirname(__file__))
STATIC_DIR = os.path.join(PKG_DIR, 'static')
GATEWAY_CONFIG_PATH = '/var/local/config/'


def static_path(static_file):
    """ Return the 'static_file' relative path """
    return os.path.join(STATIC_DIR, static_file)


_BOARD_CONFIG = {}

EXP_FILES_DIR = '/iotlab/users/{user}/.iot-lab/{exp_id}/'
EXP_FILES = {'consumption': 'consumption/{node_id}.oml',
             'radio': 'radio/{node_id}.oml',
             'event': 'event/{node_id}.oml',
             'sniffer': 'sniffer/{node_id}.oml',
             'log': 'log/{node_id}.log'}


def hostname():
    """ Return the board hostname """
    return os.uname()[1]


def default_profile():
    """ Return the default profile """
    import json
    with open(static_path('default_profile.json')) as prof:
        return json.loads(prof.read())


def board_type():
    """ Return the board type 'm3', 'a8', 'fox', or other """
    return _get_conf('board_type', GATEWAY_CONFIG_PATH, raise_error=True)


def robot_type():
    """ Return robot type None, 'roomba' """
    return _get_conf('robot', GATEWAY_CONFIG_PATH)


def _get_conf(key, path, raise_error=False):
    """
    Load config from file given as key

    :param key: config file name
    :param raise_error: select if exceptions are silenced or raised
    """
    # Singleton pattern
    if key not in _BOARD_CONFIG:
        # load from file
        try:
            _file = open(os.path.join(path, key))
            _BOARD_CONFIG[key] = _file.read().strip().lower()
            _file.close()
        except IOError as err:
            _BOARD_CONFIG[key] = None
            if raise_error:
                raise err
    return _BOARD_CONFIG[key]
