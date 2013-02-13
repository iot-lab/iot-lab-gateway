#! /usr/bin/env python

"""
FlashFirmware class
"""

import argparse
import sys


CONFIG_FILES_PATH = '~/bin'
NODES_CFG   = {
    'gwt':'fiteco-gwt.cfg',
    'm3': 'fiteco-m3.cfg',
    'a8': 'fiteco-a8.cfg'
    }

NODES = NODES_CFG.keys()




def parse_arguments(args):
    """
    Parsing arguments:

    script.py node firmware.elf
    Only pass arguments to function without script name

    """
    parser = argparse.ArgumentParser()
    parser.add_argument('node', type=str, choices=NODES,
            help="Node selection")
    parser.add_argument('firmware', type=str, help="Firmware name")
    arguments = parser.parse_args(args)

    return arguments.node, arguments.firmware




if __name__ == '__main__':
    NODE, FIRMWARE = parse_arguments(sys.argv[1:])

    print "node %s" % NODE
    print "firmware %s" % FIRMWARE
    CONFIG_FILE =  CONFIG_FILES_PATH + '/' + NODES_CFG[NODE]

    print 'config_file %s' % CONFIG_FILE




