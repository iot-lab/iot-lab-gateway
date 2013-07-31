# -*- coding:utf-8 -*-


"""
Common configuration for openocd scripts
"""


STATIC_FILES_PATH = '/var/lib/gateway_code/'
GATEWAY_CONFIG_PATH = '/var/local/config/'

NODES_CFG = {
    'gwt': {'openocd_cfg_file': 'fiteco-gwt.cfg',
            'tty': '/dev/ttyFITECO_GWT',
            'baudrate': 500000},
    'm3': {'openocd_cfg_file': 'fiteco-m3.cfg',
           'tty': '/dev/ttyFITECO_M3',
           'baudrate': 500000},
    'a8': {'openocd_cfg_file': 'fiteco-a8.cfg',
           'tty': '/dev/ttyFITECO_A8',
           'baudrate': 500000},
    }

NODES = NODES_CFG.keys()

CONTROL_NODE_SERIAL_INTERFACE = 'control_node_serial_interface'

_BOARD_CONFIG = {}


def board_type():
    """
    Return the board type 'M3' or 'A8'
    """
    if 'board_type' not in _BOARD_CONFIG:
        try:
            with open(GATEWAY_CONFIG_PATH + 'board_type') as _file:
                _BOARD_CONFIG['board_type'] = _file.read().strip()
        except IOError as err:
            raise StandardError("Could not find board type:\n  '%s'" % err)

    return _BOARD_CONFIG['board_type']


def robot_type():
    """
    Return robot type None, 'roomba'
    """
    if 'robot' not in _BOARD_CONFIG:
        try:
            with open(GATEWAY_CONFIG_PATH + 'robot') as _file:
                _BOARD_CONFIG['robot'] = _file.read().strip()
        except IOError:
            _BOARD_CONFIG['robot'] = None

    return _BOARD_CONFIG['robot']
