# -*- coding:utf-8 -*-

""" Common static configuration for the application  """

import stat
import os

STAT_0666 = (stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP |
             stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)

PKG_DIR = os.path.abspath(os.path.dirname(__file__))
STATIC_DIR = os.path.join(PKG_DIR, 'static')

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


def default_profile():
    """ Return the default profile """
    import json
    with open(static_path('default_profile.json')) as prof:
        return json.loads(prof.read())
