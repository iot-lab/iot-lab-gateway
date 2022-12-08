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

""" Open Node using JLink Segger as programmer/debugger """

import logging
import serial

from gateway_code import common
from gateway_code.common import logger_call
from gateway_code.nodes import OpenNodeBase

from gateway_code.utils.segger import Segger
from gateway_code.utils.serial_redirection import SerialRedirection

LOGGER = logging.getLogger('gateway_code')


class NodeSeggerBase(OpenNodeBase):
    # pylint:disable=no-member
    """ Open node JLink Segger implementation """

    ELF_TARGET = ('ELFCLASS32', 'EM_ARM')

    SEGGER_CLASS = Segger

    AUTOTEST_AVAILABLE = [
        'echo', 'get_time',  # mandatory
        'get_uid',
        'leds_on', 'leds_off', 'leds_blink'
    ]

    ALIM = '5V'

    def __init__(self):
        self.serial_redirection = SerialRedirection(self.TTY, self.BAUDRATE)
        self.segger = self.SEGGER_CLASS.from_node(self)

    @property
    def programmer(self):
        """Returns the segger instance of the open node."""
        return self.segger

    def clear_serial(self):
        """Clear serial link by flushing the input buffer."""
        try:
            ser = serial.Serial(self.TTY, self.BAUDRATE)
        except serial.serialutil.SerialException:
            LOGGER.error("No serial port found")
            return 1
        ser.reset_input_buffer()
        ser.close()
        return 0

    @logger_call("Node Segger: Setup of segger node")
    def setup(self, firmware_path):
        """ Flash open node, create serial redirection """
        ret_val = 0

        common.wait_no_tty(self.TTY)
        ret_val += common.wait_tty(self.TTY, LOGGER)
        ret_val += self.flash(firmware_path)
        ret_val += self.serial_redirection.start()
        return ret_val

    @logger_call("Node Segger: teardown of segger node")
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

    @logger_call("Node Segger: flash of segger node")
    def flash(self, firmware_path=None, binary=False, offset=0):
        """ Flash the given firmware on segger node

        :param firmware_path: Path to the firmware to be flashed on `node`.
                              If None, flash 'idle' firmware.
        :param binary: if True, flashes a binary file
        :param offset: the offset at which to flash the binary file
        """
        firmware_path = firmware_path or self.FW_IDLE
        LOGGER.info('Flash firmware on Segger: %s', firmware_path)
        ret_val = self.segger.flash(firmware_path, binary, offset)
        return ret_val

    @logger_call("Node Segger: reset of segger node")
    def reset(self):
        """ Reset the segger node using jtag """
        LOGGER.info('Reset segger node')
        return self.segger.reset()

    def debug_start(self):
        """ Start segger node debugger """
        LOGGER.info('segger node debugger start')
        return self.segger.debug_start()

    def debug_stop(self):
        """ Stop segger node debugger """
        LOGGER.info('segger node debugger stop')
        return self.segger.debug_stop()

    def status(self):
        """ Check segger node status """
        # Status is called when open node is not powered
        return 0
