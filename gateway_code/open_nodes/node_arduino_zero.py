# -*- coding:utf-8 -*-

# This file is a part of IoT-LAB gateway_code
# Copyright (C) 2015 INRIA (Contact: admin@iot-lab.info)
# Contributor(s) : see AUTHORS file
#
# This software is governed by the CeCILL license under French law
# and abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# http://www.cecill.info.
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.

""" Open Node Arduino Zero experiment implementation """
import logging

from gateway_code.config import static_path
from gateway_code import common
from gateway_code.common import logger_call

from gateway_code.utils.openocd import OpenOCD
from gateway_code.utils.serial_redirection import SerialRedirection

LOGGER = logging.getLogger('gateway_code')


class NodeArduinoZero(object):
    """ Open node Arduino Zero implementation """

    TYPE = 'arduino-zero'
    ELF_TARGET = ('ELFCLASS32', 'EM_ARM')
    TTY = '/dev/ttyON_ARDUINO_ZERO'
    BAUDRATE = 115200
    OPENOCD_CFG_FILE = static_path('iot-lab-arduino-zero.cfg')
    FW_IDLE = static_path('arduino_zero_idle.elf')
    FW_AUTOTEST = static_path('arduino_zero_autotest.elf')

    AUTOTEST_AVAILABLE = [
        'echo', 'get_time',  # mandatory
        'leds_on', 'leds_off'
    ]

    ALIM = '5V'
    FLASH_TIMEOUT = 60  # Got 40 seconds at max with riot gnrc_networking

    def __init__(self):
        self.serial_redirection = SerialRedirection(self.TTY, self.BAUDRATE)
        self.openocd = OpenOCD.from_node(self, timeout=self.FLASH_TIMEOUT)

    @logger_call("Node Arduino Zero : Setup of arduino zero node")
    def setup(self, firmware_path):
        """ Flash open node, create serial redirection """
        ret_val = 0

        common.wait_no_tty(self.TTY)
        ret_val += common.wait_tty(self.TTY, LOGGER)
        ret_val += self.flash(firmware_path)
        ret_val += self.serial_redirection.start()
        return ret_val

    @logger_call("Node Arduino Zero : teardown of arduino zero node")
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

    @logger_call("Node Arduino Zero : flash of arduino zero node")
    def flash(self, firmware_path=None):
        """ Flash the given firmware on Arduino Zero node

        :param firmware_path: Path to the firmware to be flashed on `node`.
                              If None, flash 'idle' firmware.
        """
        firmware_path = firmware_path or self.FW_IDLE
        LOGGER.info('Flash firmware on Arduino Zero: %s', firmware_path)
        return self.openocd.flash(firmware_path)

    @logger_call("Node Arduino Zero : reset of arduino zero node")
    def reset(self):
        """ Reset the Arduino Zero node using jtag """
        LOGGER.info('Reset Arduino Zero node')
        return self.openocd.reset()

    def debug_start(self):
        """ Start Arduino Zero node debugger """
        LOGGER.info('Arduino Zero Node debugger start')
        return self.openocd.debug_start()

    def debug_stop(self):
        """ Stop Arduino Zero node debugger """
        LOGGER.info('Arduino Zero Node debugger stop')
        return self.openocd.debug_stop()

    @staticmethod
    def status():
        """ Check Arduino Zero node status """
        # Status is called when open node is not powered
        # So can't check for FTDI
        return 0
