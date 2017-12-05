# -*- coding:utf-8 -*-
""" Blank file for the implementation of an open-node called Nodename """

import logging

from gateway_code.config import static_path
from gateway_code.common import logger_call


LOGGER = logging.getLogger('gateway_code')


class NodeExample(object):
    """ Example node """

    TTY = '/dev/ttyON_EXAMPLE'
    # The tty as named in the udev rule
    BAUDRATE = 9600
    # The baudrate used to communicate with the open-node on the serial port
    FW_IDLE = static_path('example_idle.elf')
    # The name of the idle firmware
    FW_AUTOTEST = static_path('example_autotest.elf')
    # The name of the autotest firmware
    ALIM = '5V'
    # The tension of alimentation (will be 5V in most of the case)

    AUTOTEST_AVAILABLE = ['echo']

    # The list of autotest available for your node.
    # As describe in the document,
    # this list must contain at least 'echo'

    def __init__(self):
        pass
        # The initialization of your class

    @logger_call("Node Example : Setup of example")
    def setup(self, firmware_path):
        # Here you will perform all the necessary action needed
        # by your node before the start of an experiment.
        return 1

    @logger_call("Node Example : teardown of example node")
    def teardown(self):
        # Here you will perform all the necessary action to
        # properly terminate your node
        return 1

    @logger_call("Node Example : flash of example node")
    def flash(self, firmware_path=None):
        # Here
        return 1

    @logger_call("Node Example : reset of example node")
    def reset(self):
        # Not implemented
        return 1

    def debug_start(self):
        # Here you will start the debug of your node
        return 1

    def debug_stop(self):
        # Here you will stop the debug of your node
        return 1

    @staticmethod
    def status():
        # Here you will check the health of the node (for exemple with ftdi chip)
        # if you are unable to check it, just return 0
        return 0