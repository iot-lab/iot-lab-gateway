# -*- coding:utf-8 -*-

"""
Common static configuration for the application and `OpenOCD`

:STATIC_FILES_PATH: Static files path (default firmware, profile, openocd conf)
:GATEWAY_CONFIG_PATH: Board specific configuraion files path
:CONTROL_NODE_SERIAL_INTERFACE: Control node serial programe name
:NODES: Nodes name
:NODES_CFG: Per node OpenOCD and serial configuration
"""

import stat
STAT_0666 = (stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP |
             stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)

STATIC_FILES_PATH = '/var/lib/gateway_code/'
GATEWAY_CONFIG_PATH = '/var/local/config/'

NODES_CFG = {
    'gwt': {'openocd_cfg_file': 'iot-lab-cn.cfg',
            'tty': '/dev/ttyCN',
            'baudrate': 500000},
    'm3': {'openocd_cfg_file': 'iot-lab-m3.cfg',
           'tty': '/dev/ttyON_M3',
           'baudrate': 500000},
    'a8': {'openocd_cfg_file': 'iot-lab-a8-m3.cfg',
           'tty': '/dev/ttyA8_M3',
           'baudrate': 500000},
    }

OPEN_A8_CFG = {
    'tty': '/dev/ttyON_A8',
    'baudrate': 115200
    }

NODES = NODES_CFG.keys()

ROOMBA_CFG = {'tty': '/dev/ttyROOMBA'}

CONTROL_NODE_SERIAL_INTERFACE = 'control_node_serial_interface'

FIRMWARES = {
    'idle': STATIC_FILES_PATH + 'idle.elf',
    'control_node': STATIC_FILES_PATH + 'control_node.elf',
    'm3_autotest': STATIC_FILES_PATH + 'm3_autotest.elf',
    'a8_autotest': STATIC_FILES_PATH + 'a8_autotest.elf'
    }

_BOARD_CONFIG = {}

EXP_FILES_DIR = '/iotlab/users/{user}/.iot-lab/{exp_id}/'
EXP_FILES = {'consumption': 'consumption/{node_id}.oml',
             'radio': 'radio/{node_id}.oml',
             'event': 'event/{node_id}.oml',
             'sniffer': 'sniffer/{node_id}.oml',
             'log': 'log/{node_id}.log'}


def hostname():
    """ Return the board hostname """
    import socket
    return socket.gethostname()


def default_profile():
    """ Return the default profile """
    import json
    _profile_str = _get_conf('default_profile.json', STATIC_FILES_PATH,
                             raise_error=True)
    return json.loads(_profile_str)


def board_type():
    """ Return the board type 'M3' or 'A8' """
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
            _file = open(path + key)
            _BOARD_CONFIG[key] = _file.read().strip()
            _file.close()
        except IOError as err:
            _BOARD_CONFIG[key] = None
            if raise_error:
                raise err
    return _BOARD_CONFIG[key]
