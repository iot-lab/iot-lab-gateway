# -*- coding:utf-8 -*-
""" Blank file for the implemention of an open-node called firefly """

import logging

from gateway_code.config import static_path
from gateway_code import common
from gateway_code.common import logger_call

from gateway_code.utils.CC2538 import CC2538
from gateway_code.utils.serial_redirection import SerialRedirection


LOGGER = logging.getLogger('gateway_code')


class NodeFirefly(object):
    """Open node firefly implementation"""

    TYPE = 'firefly'
    ELF_TARGET = ('ELFCLASS32', 'EM_ARM')

    TTY = '/dev/ttyON_firefly'
    # The tty as named in the udev rule
    BAUDRATE = 115200
    PROGRAM_BAUDRATE = 460800
    # The baudrate used to communicate with the open-node on the serial port
    FW_IDLE = static_path('idle_firefly.elf')
    # The name of the idle firmware
    FW_AUTOTEST = static_path('firefly_autotest.elf')
    # The name of the autotest firmware
    ALIM = '5V'
    # The tension of alimentation (will be 5V in most of the case)
    TTY_READY_DELAY = 1

    FIREFLY_CONF = {
        'port': TTY,
        'baudrate': PROGRAM_BAUDRATE,
    }
    AUTOTEST_AVAILABLE = ['echo', 'get_time',  # mandatory
                          'leds_on', 'leds_off', 'leds_blink']

    # The list of autotest available for your node.
    # As describe in the document,
    # this list must contain at least 'echo'

    def __init__(self):
        # The initialization of your class
        self.serial_redirection = SerialRedirection(self.TTY, self.BAUDRATE)
        self.firefly = CC2538(self.FIREFLY_CONF)

    @logger_call("Node firefly : Setup of firefly node")
    def setup(self, firmware_path):
        """ Flash open node, create serial redirection """
        ret_val = 0

        common.wait_no_tty(self.TTY)
        ret_val += common.wait_tty(self.TTY, LOGGER)
        ret_val += self.flash(firmware_path)
        ret_val += self.serial_redirection.start()
        return ret_val

    @logger_call("Node firefly : Teardown of firefly node")
    def teardown(self):
        """ Stop serial redirection and flash idle firmware """
        ret_val = 0

        common.wait_no_tty(self.TTY)
        ret_val += common.wait_tty(self.TTY, LOGGER)
        ret_val += self.serial_redirection.stop()
        ret_val += self.flash(None)
        return ret_val

    @logger_call("Node firefly : flash of firefly node")
    def flash(self, firmware_path=None):
        """ Flash the given firmware on firefly node

        :param firmware_path: Path to the firmware to be flashed on `node`.
                              If None, flash 'idle' firmware.
        """
        firmware_path = firmware_path or self.FW_IDLE
        LOGGER.info('Flash firmware on firefly: %s', firmware_path)
        LOGGER.info('Firmware path : %s -- Firmware idle path : %s',
                    firmware_path, self.FW_IDLE)
        return self.firefly.flash(firmware_path)

    @logger_call("Node firefly : reset of firefly node")
    def reset(self):
        """ Reset the firefly node using jtag """
        LOGGER.info('Reset firefly node')
        return self.firefly.reset()

    def debug_start(self):
        """ Start firefly node debugger """
        LOGGER.info('firefly Node debugger start')
        return self.firefly.debug_start()

    def debug_stop(self):
        """ Stop firefly node debugger """
        LOGGER.info('firefly Node debugger stop')
        return self.firefly.debug_stop()

    @staticmethod
    def status():
        """ Check your node """
        # Here you will check your node (for exemple with ftdi chip)
        # if you are unable to check your node, just return 0
        return 0
