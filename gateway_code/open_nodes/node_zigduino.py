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

""" Open Node Zigduino r2 experiment implementation """

import time
import logging

import termios
import serial
from serial import SerialException

from gateway_code.config import static_path
from gateway_code import common
from gateway_code.common import logger_call
from gateway_code.nodes import OpenNodeBase

from gateway_code.utils.avrdude import AvrDude
from gateway_code.utils.serial_redirection import SerialRedirection

LOGGER = logging.getLogger('gateway_code')


class NodeZigduino(OpenNodeBase):
    """Open node Zigduino implementation."""

    TYPE = "zigduino"
    ELF_TARGET = ('ELFCLASS32', 'EM_AVR')
    TTY = '/dev/iotlab/ttyON_ZIGDUINO'
    BAUDRATE = 57600
    FW_IDLE = static_path('zigduino_idle.elf')
    FW_AUTOTEST = static_path('zigduino_autotest.elf')
    AVRDUDE_CONF = {
        'tty': TTY,
        'baudrate': 57600,
        'model': 'atmega128rfa1',
        'programmer': 'arduino',
        'hex_prefix': '',
        'flash_opts': '-D',
    }

    AUTOTEST_AVAILABLE = [
        'echo', 'get_time'  # mandatory
    ]

    ALIM = '5V'

    def __init__(self):
        self.serial_redirection = SerialRedirection(self.TTY, self.BAUDRATE)
        self.avrdude = AvrDude(self.AVRDUDE_CONF)

    @property
    def programmer(self):
        """Returns the avrdude programmer instance of the open node."""
        return self.avrdude

    def disable_dtr(self):
        """ Disable serial port DTR in order to avoid
            board autoreset at first connection
        """
        # Check if Zigduino is up before DTR reset
        try:
            ser = serial.Serial(self.TTY, self.BAUDRATE)
        except SerialException:
            LOGGER.error("No serial port found")
            return 1
        with open(self.TTY) as ser:
            attrs = termios.tcgetattr(ser)
            attrs[2] = attrs[2] & ~termios.HUPCL
            termios.tcsetattr(ser, termios.TCSAFLUSH, attrs)
        return 0

    @logger_call("Setup of Zigduino node")
    def setup(self, firmware_path):
        """ Flash open node, create serial redirection """
        ret_val = 0
        # it appears that /dev/ttyON_ZIGDUINO need some time to be detected
        common.wait_no_tty(self.TTY, timeout=common.TTY_DETECT_TIME)
        ret_val += common.wait_tty(self.TTY, LOGGER,
                                   timeout=common.TTY_DETECT_TIME)
        ret_val += self.do_flash(firmware_path, redirect=False)
        ret_val += self.disable_dtr()
        ret_val += self.serial_redirection.start()
        return ret_val

    @logger_call("Teardown of Zigduino node")
    def teardown(self):
        """ Stop serial redirection and flash idle firmware """
        ret_val = 0

        common.wait_no_tty(self.TTY, timeout=common.TTY_DETECT_TIME)
        ret_val += common.wait_tty(
            self.TTY, LOGGER, timeout=common.TTY_DETECT_TIME)
        ret_val += self.serial_redirection.stop()
        # Reboot needs 8 seconds before ending linux sees it in < 2 seconds
        ret_val += common.wait_tty(self.TTY, LOGGER, timeout=10)
        ret_val += self.do_flash(None, redirect=False)
        return ret_val

    def flash(self, firmware_path=None, binary=False, offset=0):
        """ Flash the given firmware on Zigduino node
        :param firmware_path: Path to the firmware to be flashed on `node`.
            If None, flash 'idle' firmware
        :param binary: whether to flash a binary file
        :param offset: at which offset to flash the binary file
        :param redirect: whether to stop the serial redirection before flashing
        """
        return self.do_flash(firmware_path, binary, offset, True)

    @logger_call("Flash of Zigduino node")
    def do_flash(self, firmware_path=None, binary=False,
                 offset=0, redirect=True):  # pylint:disable=unused-argument
        """ Flash the given firmware on Zigduino node
        :param firmware_path: Path to the firmware to be flashed on `node`.
            If None, flash 'idle' firmware
        :param binary: whether to flash a binary file
        :param offset: at which offset to flash the binary file
        :param redirect: whether to stop the serial redirection before flashing
        """
        if binary:
            LOGGER.error('FLASH: binary mode not supported with Zigduino')
            return 1

        if offset != 0:
            LOGGER.error('FLASH: flash offset is not supported with Zigduino')
            return 1

        ret_val = 0
        firmware_path = firmware_path or self.FW_IDLE
        LOGGER.info('Flash firmware on Zigduino: %s', firmware_path)
        # First stop serial redirection, flash hangup if an
        # user session is openened on port 20000
        common.wait_no_tty(self.TTY, timeout=common.TTY_DETECT_TIME)
        ret_val += common.wait_tty(
            self.TTY, LOGGER, timeout=common.TTY_DETECT_TIME)
        if redirect:
            ret_val += self.serial_redirection.stop()
        # Then flash
        ret_val += self.avrdude.flash(firmware_path)
        ret_val += common.wait_tty(self.TTY, LOGGER, timeout=10)
        # Finally restore serial redirection
        if redirect:
            ret_val += self.disable_dtr()
            ret_val += self.serial_redirection.start()
        LOGGER.info("end flash")
        return ret_val

    @logger_call("Reset of Zigduino node")
    def reset(self):
        """ Reset the Zigduino node using DTR"""
        ret_val = 0

        # Check if Zigduino is up before DTR reset
        try:
            ser = serial.Serial(self.TTY, self.BAUDRATE)
        except SerialException:
            LOGGER.error("No serial port found")
            return 1

        try:
            ser.setDTR(False)
            time.sleep(0.5)
            ser.setDTR(True)
            time.sleep(0.5)
            ser.close()
        except OSError:
            LOGGER.warning("Nothing to reset")
        ret_val += common.wait_tty(self.TTY, LOGGER, timeout=10)
        return ret_val

    @staticmethod
    def status():
        """ Check Zigduino node status """
        # It's impossible for us to check the status of the zigduino node
        return 0
