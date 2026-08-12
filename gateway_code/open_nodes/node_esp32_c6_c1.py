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

"""
    Open Node Espressif ESP32-C6-DevKitC-1 
"""

import time
import logging
import os
import shlex

import termios
import serial
from serial import SerialException

import RPi.GPIO as GPIO

from gateway_code.config import static_path
from gateway_code import common
from gateway_code.common import logger_call
from gateway_code.open_nodes.common.node_bin import NodeBinBase

from gateway_code.utils.esp import Esp
from gateway_code.utils.serial_redirection import SerialRedirection

from gateway_code.utils import subprocess_timeout


LOGGER = logging.getLogger('gateway_code')


class NodeEsp32C6C1(NodeBinBase):
    """Open node ESP32-C6C1 implementation."""
    TYPE = "esp32_c6c1"
    TTY = '/dev/iotlab/ttyON_ESP32C6C1'
    ELF_TARGET = ('ELFCLASS32', 'EM_XTENSA')
    BAUDRATE = 115200
    FW_IDLE = static_path('esp32-c6c1_idle.bin')
    FW_AUTOTEST = static_path('esp32-c6c1_autotest.bin')

    OFFSET = 0x00000
    GPIO_RESET = 17 # Raspberry (11 pin)

    ESPTOOL_CONF = {
        'tty': TTY,
        'baudrate': 921600,
        'chip': 'esp32-c6' 
    }

    AUTOTEST_AVAILABLE = [
        'echo', 'get_time'  # mandatory
    ]

    ALIM = '5V'

    def __init__(self):
        self.serial_redirection = SerialRedirection(
            self.TTY, self.BAUDRATE, serial_opts=("echo=0", "raw", "crnl")
        )
        self.esp = Esp(self.ESPTOOL_CONF)

    @property
    def programmer(self):
        """Returns the esp programmer instance of the open node."""
        return self.esp

    @logger_call("Setup of ESP32-C6C1 node")
    def setup(self, firmware_path):
        """ Flash open node, create serial redirection """
        ret_val = 0
        common.wait_no_tty(self.TTY, timeout=common.TTY_DETECT_TIME)
        ret_val += common.wait_tty(self.TTY, LOGGER,
                                   timeout=common.TTY_DETECT_TIME)
        ret_val += self.do_flash(firmware_path, redirect=False)
        ret_val += self.serial_redirection.start()
        return ret_val

    @logger_call("Teardown of ESP32-C6C1 node")
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

    def flash(self, firmware_path=None, binary=False, offset=int(OFFSET)):
        """ Flash the given firmware on ESP32-C6C1 node
        :param firmware_path: Path to the firmware to be flashed on `node`.
            If None, flash 'idle' firmware
        :param binary: whether to flash a binary file
        :param offset: at which offset to flash the binary file
        :param redirect: whether to stop the serial redirection before flashing
        """
        return self.do_flash(firmware_path, binary, offset, True)

    @logger_call("Flash of ESP32-C6C1 node")
    def do_flash(self, firmware_path=None, binary=False,
                 offset=int(OFFSET), redirect=True):  # pylint:disable=unused-argument
        """ Flash the given firmware on ESP32-C6C1 node
        :param firmware_path: Path to the firmware to be flashed on `node`.
            If None, flash 'idle' firmware
        :param binary: whether to flash a binary file
        :param offset: at which offset to flash the binary file
        :param redirect: whether to stop the serial redirection before flashing
        """

        ret_val = 0
        if firmware_path is None:
            binary = True
        firmware_path = firmware_path or self.FW_IDLE
        LOGGER.info('Flash firmware on ESP32-C6C1: %s', firmware_path)
        # First stop serial redirection, flash hangup if an
        # user session is openened on port 20000
        common.wait_no_tty(self.TTY, timeout=common.TTY_DETECT_TIME)
        ret_val += common.wait_tty(
            self.TTY, LOGGER, timeout=common.TTY_DETECT_TIME)
        if redirect:
            ret_val += self.serial_redirection.stop()
        # Then flash
        time.sleep(1)
        ret_val += self.esp.flash(firmware_path, binary, offset)
        ret_val += common.wait_tty(self.TTY, LOGGER, timeout=20)
        # Finally restore serial redirection
        if redirect:
            ret_val += self.serial_redirection.start()
        LOGGER.info("end flash")
        return ret_val

    @logger_call("Reset of ESP32-C6C1 node")
    def reset(self):
        """ Reset the ESP32-C6C1 """
        ret_val = 0
        ret_val += self.esp_reset()
        return ret_val

    @logger_call("ESP32-C6C1: Reset OpenNode")
    def esp_reset(self):
        """ Hard reset board """
        LOGGER.debug("Reset ESP32-C6C1 board")
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.GPIO_RESET, GPIO.OUT)
        time.sleep(0.2)
        GPIO.output(self.GPIO_RESET, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(self.GPIO_RESET, GPIO.LOW)
        time.sleep(0.2)
        GPIO.cleanup()
        return 0

    @staticmethod
    def status():
        """ Check ESP32-C6C1 node status """
        # It's impossible for us to check the status of the ESP32-C6C1 node
        return 0
