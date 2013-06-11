# -*- coding:utf-8 -*-


"""
Common configuration for openocd scripts
"""


STATIC_FILES_PATH = '/var/lib/gateway_code/'
NODES_CFG   = {
        'gwt': { 'openocd_cfg_file':'fiteco-gwt.cfg',
            'tty':'/dev/ttyFITECO_GWT', 'baudrate':500000},
        'm3': { 'openocd_cfg_file':'fiteco-m3.cfg',
            'tty':'/dev/ttyFITECO_M3',  'baudrate':500000},
        'a8': { 'openocd_cfg_file':'fiteco-a8.cfg',
            'tty':'/dev/ttyFITECO_A8',  'baudrate':500000},
    }

NODES = NODES_CFG.keys()

CONTROL_NODE_SERIAL_INTERFACE = 'control_node_serial_interface'

