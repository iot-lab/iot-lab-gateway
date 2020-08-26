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

""" Open Node Atmega256RFR2 Xplained Pro experiment implementation """

import logging

from gateway_code.config import static_path
from gateway_code import common
from gateway_code.common import logger_call
from gateway_code.nodes import OpenNodeBase

from gateway_code.utils.avrdude import AvrDude
from gateway_code.utils.serial_redirection import SerialRedirection

LOGGER = logging.getLogger('gateway_code')


class NodeAtmega256rfr2(OpenNodeBase):
    """Open node Atmega256RFR2 Xplained Pro implementation."""

    TYPE = 'atmega256rfr2'
    ELF_TARGET = ('ELFCLASS32', 'EM_AVR')
    TTY = '/dev/iotlab/ttyON_CMSIS_DAP'
    BAUDRATE = 115200
    FW_IDLE = static_path('atmega256rfr2_idle.elf')
    FW_AUTOTEST = static_path('atmega256rfr2_autotest.elf')
    AVRDUDE_CONF = {
        'tty': None,
        'baudrate': None,
        'model': 'm256rfr2',
        'programmer': 'xplainedpro',
        'hex_prefix': 'flash:w:',
        'flash_opts': '',
    }

    AUTOTEST_AVAILABLE = [
        'echo', 'get_time',  # mandatory
        'get_uid',
        'leds_on', 'leds_off', 'leds_blink'
    ]

    ALIM = '5V'

    def __init__(self):
        self.serial_redirection = SerialRedirection(self.TTY, self.BAUDRATE)
        self.avrdude = AvrDude(self.AVRDUDE_CONF)

    @property
    def programmer(self):
        """Returns the avrdude programmer instance of the open node."""
        return self.avrdude

    @logger_call("Node Atmega256RFR2 : Setup of atmega256rfr2 node")
    def setup(self, firmware_path):
        """Flash open node, create serial redirection."""
        ret_val = 0
        common.wait_no_tty(self.TTY)
        ret_val += common.wait_tty(self.TTY, LOGGER)
        ret_val += self.serial_redirection.start()
        ret_val += self.flash(firmware_path)
        return ret_val

    @logger_call("Node Atmega256RFR2 : Teardown of atmega256rfr2 node")
    def teardown(self):
        """Stop serial redirection and flash idle firmware."""
        ret_val = 0
        common.wait_no_tty(self.TTY)
        ret_val += common.wait_tty(self.TTY, LOGGER)
        ret_val += self.serial_redirection.stop()
        ret_val += self.flash(None)
        return ret_val

    @logger_call("Node Atmega256RFR2 : Flash of atmega256rfr2 node")
    def flash(self, firmware_path=None, binary=False, offset=0):
        """Flash the given firmware on Atmega256RFR2 node

        :param firmware_path: Path to the firmware to be flashed on `node`.
                              If None, flash 'idle' firmware
        :param binary: whether to flash a binary file
        :param offset: at which offset to flash the binary file """
        if binary:
            LOGGER.error(
                'FLASH: binary mode not supported with Atmega256RFR2')
            return 1
        if offset != 0:
            LOGGER.error(
                'FLASH: flash offset is not supported with Atmega256RFR2')
            return 1

        ret_val = 0
        firmware_path = firmware_path or self.FW_IDLE
        LOGGER.info('Flash firmware on Atmega256RFR2: %s', firmware_path)
        ret_val += self.avrdude.flash(firmware_path)

        return ret_val

    @logger_call("Node Atmega256RFR2 : Reset of atmega256rfr2 node")
    def reset(self):
        """Reset the Atmega256RFR2 node using avrdude."""
        ret_val = 0
        ret_val += self.avrdude.reset()
        return ret_val

    @staticmethod
    def status():
        """Check Atmega256RFR2 node status."""
        # It's impossible for us to check the status of the atmega256rfr2 node
        return 0
