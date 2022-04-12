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
""" contains an implementation of The Zolertia Firefly open node"""

import logging

from gateway_code.config import static_path
from gateway_code import common
from gateway_code.common import logger_call

from gateway_code.utils.cc2538 import CC2538
from gateway_code.nodes import OpenNodeBase
from gateway_code.utils.serial_redirection import SerialRedirection

LOGGER = logging.getLogger('gateway_code')


class NodeFirefly(OpenNodeBase):
    """ implementation of The Zolertia Firefly open node"""
    TYPE = 'firefly'
    ELF_TARGET = ('ELFCLASS32', 'EM_ARM')

    TTY = '/dev/iotlab/ttyON_FIREFLY'
    # The tty as named in the udev rule
    BAUDRATE = 115200
    PROGRAM_BAUDRATE = 460800
    # The baudrate used to communicate with the open-node on the serial port
    FW_IDLE = static_path('firefly_idle.elf')
    # The name of the idle firmware
    FW_AUTOTEST = static_path('firefly_autotest.elf')
    # The name of the autotest firmware
    ALIM = '5V'
    # The tension of alimentation (will be 5V in most of the case)
    TTY_READY_DELAY = 1

    FIREFLY_CONF = {'port': TTY,
                    'baudrate': PROGRAM_BAUDRATE}
    AUTOTEST_AVAILABLE = ['echo', 'get_time', 'get_uid',
                          'leds_on', 'leds_off', 'leds_blink']

    # The list of autotest available for your node.
    # As describe in the document,
    # this list must contain at least 'echo'

    def __init__(self):
        # The initialization of your class
        self.serial_redirection = SerialRedirection(self.TTY, self.BAUDRATE)
        self.cc2538 = CC2538(self.FIREFLY_CONF)

    @property
    def programmer(self):
        """Returns the cc2538 programmer instance of the open node."""
        return self.cc2538

    @logger_call("Node firefly : Setup of firefly node")
    def setup(self, firmware_path):
        """ Flash open node, create serial redirection """
        ret_val = 0

        common.wait_no_tty(self.TTY)
        ret_val += common.wait_tty(self.TTY, LOGGER)
        ret_val += self.do_flash(firmware_path, toggle_redirect=False)
        ret_val += self.serial_redirection.start()
        return ret_val

    @logger_call("Node firefly : Teardown of firefly node")
    def teardown(self):
        """ Stop serial redirection and flash idle firmware """
        ret_val = 0

        common.wait_no_tty(self.TTY)
        ret_val += common.wait_tty(self.TTY, LOGGER)
        ret_val += self.serial_redirection.stop()
        ret_val += self.do_flash(None, toggle_redirect=False)
        return ret_val

    def flash(self, firmware_path=None, binary=False, offset=0):
        """Flash the given firmware on Firefly."""
        if binary:
            LOGGER.error('FLASH: binary mode not supported with Firefly')
            return 1

        if offset != 0:
            LOGGER.error('FLASH: flash offset is not supported with Firefly')
            return 1

        return self.do_flash(firmware_path, True)

    @logger_call("Node firefly : flash of firefly node")
    def do_flash(self, firmware_path=None, toggle_redirect=True):
        """ Flash the given firmware on firefly node

        :param firmware_path: Path to the firmware to be flashed on `node`.
                              If None, flash 'idle' firmware.
        """
        firmware_path = firmware_path or self.FW_IDLE
        LOGGER.info('Flash firmware on firefly: %s', firmware_path)
        LOGGER.info('Firmware path : %s -- Firmware idle path : %s',
                    firmware_path, self.FW_IDLE)
        ret_val = 0
        if toggle_redirect:
            ret_val += self.serial_redirection.stop()
        ret_val += self.cc2538.flash(firmware_path)
        if toggle_redirect:
            ret_val += self.serial_redirection.start()
        return ret_val

    @logger_call("Node firefly : reset of firefly node")
    def reset(self):
        """ Reset the firefly node using jtag """
        LOGGER.info('Reset firefly node')
        return self.cc2538.reset()

    def status(self):
        """ check the node status """
        return 0
