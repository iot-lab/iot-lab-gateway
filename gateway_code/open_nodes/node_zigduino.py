# -*- coding:utf-8 -*-
""" Open Node Zigduino r2 experiment implementation """

import time
import logging

import serial

from gateway_code.config import static_path
from gateway_code import common
from gateway_code.common import logger_call

from gateway_code.utils.avrdude import AvrDude
from gateway_code.utils.serial_redirection import SerialRedirection

LOGGER = logging.getLogger('gateway_code')


class NodeZigduino(object):
    """Open node Zigduino implemention."""

    TYPE = "zigduino"
    ELF_TARGET = ('ELFCLASS32', 'EM_AVR')
    TTY = '/dev/ttyON_ZIGDUINO'
    BAUDRATE = 57600
    FW_IDLE = static_path('idle_zigduino.elf')
    FW_AUTOTEST = static_path('zigduino_autotest.elf')
    AVRDUDE_CONF = {
        'tty': TTY,
        'baudrate': 57600,
        'model': 'atmega128rfa1',
        'programmer': 'arduino',
    }

    AUTOTEST_AVAILABLE = [
        'echo', 'get_time'  # mandatory
    ]

    ALIM = '5V'

    def __init__(self):
        self.serial_redirection = SerialRedirection(self.TTY, self.BAUDRATE)
        self.avrdude = AvrDude(self.AVRDUDE_CONF)

    @logger_call("Setup of Zigduino node")
    def setup(self, firmware_path):
        """ Flash open node, create serial redirection """
        ret_val = 0
        # it appears that /dev/ttyON_ZIGDUINO need some time to be detected
        common.wait_no_tty(self.TTY, timeout=common.TTY_DETECT_TIME)
        ret_val += common.wait_tty(self.TTY, LOGGER,
                                   timeout=common.TTY_DETECT_TIME)
        ret_val += self.flash(firmware_path, redirect=False)
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
        ret_val += self.flash(None, redirect=False)
        return ret_val

    @logger_call("Flash of Zigduino node")
    def flash(self, firmware_path=None, redirect=True):
        """ Flash the given firmware on Zigduino node
        :param firmware_path: Path to the firmware to be flashed on `node`.
            If None, flash 'idle' firmware """
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
            ret_val += self.serial_redirection.start()
        LOGGER.info("end flash")
        return ret_val

    @logger_call("Reset of Zigduino node")
    def reset(self):
        """ Reset the Zigduino node using DTR"""
        ret_val = 0
        try:
            ser = serial.Serial(self.TTY, self.BAUDRATE)
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
        # It's impossible for us to check the status of the mega node
        return 0
