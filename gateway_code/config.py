# -*- coding:utf-8 -*-

"""
Common static configuration for the application and `OpenOCD`

:STATIC_FILES_PATH: Static files path (default firmware, profile, openocd conf)
:GATEWAY_CONFIG_PATH: Board specific configuraion files path
:CONTROL_NODE_SERIAL_INTERFACE: Control node serial programe name
:NODES: Nodes name
:NODES_CFG: Per node OpenOCD and serial configuration
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

ROOMBA_CFG = {'tty': '/dev/ttyROOMBA'}

CONTROL_NODE_SERIAL_INTERFACE = 'control_node_serial_interface'

FIRMWARES = {
    'idle': STATIC_FILES_PATH + 'idle.elf',
    'control_node': STATIC_FILES_PATH + 'control_node.elf',
    }

_BOARD_CONFIG = {}


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
