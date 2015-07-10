# -*- coding:utf-8 -*-
""" Open Node FOX experiment implementation """

from gateway_code.config import static_path
from gateway_code import common
from gateway_code.common import logger_call

from gateway_code.utils.openocd import OpenOCD
from gateway_code.utils.serial_redirection import SerialRedirection

import logging
LOGGER = logging.getLogger('gateway_code')


class NodeFox(object):

    """ Open node FOX implemention """
    # Contrary to m3 node, fox node need some time to be visible.
    # Also flash/reset may fail after a node start_dc but don't care
    TTY = '/dev/ttyON_FOX'
    BAUDRATE = 500000
    OPENOCD_CFG_FILE = static_path('iot-lab-fox.cfg')
    FW_IDLE = static_path('idle_fox.elf')
    FW_AUTOTEST = static_path('fox_autotest.elf')
    ALIM = '5V'

    def __init__(self):
        self.serial_redirection = SerialRedirection(self.TTY, self.BAUDRATE)
        self.openocd = OpenOCD(self.OPENOCD_CFG_FILE)

    @logger_call("Node Fox : Setup of fox node")
    def setup(self, firmware_path):
        """ Flash open node, create serial redirection """
        ret_val = 0

        common.wait_no_tty(self.TTY)
        ret_val += common.wait_tty(self.TTY, LOGGER)
        ret_val += self.flash(firmware_path)
        ret_val += self.serial_redirection.start()
        return ret_val

    @logger_call("Node Fox : teardown of fox node")
    def teardown(self):
        """ Stop serial redirection and flash idle firmware """
        ret_val = 0
        # ON may have been stopped at the end of the experiment.
        # And then restarted again in cn teardown.
        # This leads to problem where the TTY disappears and reappears during
        # the first 2 seconds. So let some time if it wants to disappear first.
        common.wait_no_tty(self.TTY)
        ret_val += common.wait_tty(self.TTY, LOGGER)
        # cleanup debugger before flashing
        ret_val += self.debug_stop()
        ret_val += self.serial_redirection.stop()
        ret_val += self.flash(None)
        return ret_val

    @logger_call("Node Fox : flash of fox node")
    def flash(self, firmware_path=None):
        """ Flash the given firmware on FOX node
        :param firmware_path: Path to the firmware to be flashed on `node`.
            If None, flash 'idle' firmware.
        """
        firmware_path = firmware_path or self.FW_IDLE
        LOGGER.info('Flash firmware on FOX: %s', firmware_path)
        return self.openocd.flash(firmware_path)

    @logger_call("Node Fox : reset of fox node")
    def reset(self):
        """ Reset the FOX node using jtag """
        LOGGER.info('Reset FOX node')
        return self.openocd.reset()

    def debug_start(self):
        """ Start FOX node debugger """
        LOGGER.info('FOX Node debugger start')
        return self.openocd.debug_start()

    def debug_stop(self):
        """ Stop FOX node debugger """
        LOGGER.info('FOX Node debugger stop')
        return self.openocd.debug_stop()

    @staticmethod
    def status():
        """ Check FOX node status """
        # Status is called when open node is not powered
        # So can't check for FTDI
        return 0
