# -*- coding:utf-8 -*-
""" Open Node Mega experiment implementation """

from gateway_code.config import static_path
from gateway_code import common
from gateway_code.common import logger_call

from gateway_code.utils.avrdude import AvrDude
from gateway_code.utils.serial_redirection import SerialRedirection

import serial

import logging
LOGGER = logging.getLogger('gateway_code')


class NodeMega(object):

    """ Open node Mega implemention """
    TTY = '/dev/ttyON_MEGA'
    BAUDRATE = 57600
    FW_IDLE = static_path('idle_mega.elf')
    FW_AUTOTEST = static_path('mega_autotest.elf')
    AVRDUDE_CONF = {
        'tty': TTY,
        'baudrate': 115200,
        'model': 'atmega2560',
        'programmer': 'wiring',
    }

    AUTOTEST_AVAILABLE = ['test_echo',
                          'test_time',
                          'test_uid',
                          ]

    ALIM = '5V'

    def __init__(self):
        self.serial_redirection = SerialRedirection(self.TTY, self.BAUDRATE)
        self.avrdude = AvrDude(self.AVRDUDE_CONF)

    @logger_call("Setup of mega node")
    def setup(self, firmware_path):
        """ Flash open node, create serial redirection """
        ret_val = 0
        # it appears that /dev/ttyON_MEGA need some time to be detected
        common.wait_no_tty(self.TTY, timeout=common.TTY_DETECT_TIME)
        ret_val += common.wait_tty(self.TTY, LOGGER,
                                   timeout=common.TTY_DETECT_TIME)
        ret_val += self.flash(firmware_path)
        ret_val += self.serial_redirection.start()
        return ret_val

    @logger_call("Teardown of mega node")
    def teardown(self):
        """ Stop serial redirection and flash idle firmware """
        ret_val = 0

        common.wait_no_tty(self.TTY, timeout=common.TTY_DETECT_TIME)
        ret_val += common.wait_tty(
            self.TTY, LOGGER, timeout=common.TTY_DETECT_TIME)
        ret_val += self.serial_redirection.stop()
        # Reboot needs 8 seconds before ending linux sees it in < 2 seconds
        ret_val += common.wait_tty(self.TTY, LOGGER, timeout=10)
        ret_val += self.flash(None)
        return ret_val

    @logger_call("Flash of mega node")
    def flash(self, firmware_path=None):
        """ Flash the given firmware on Mega node
        :param firmware_path: Path to the firmware to be flashed on `node`.
            If None, flash 'idle' firmware """
        ret_val = 0
        firmware_path = firmware_path or self.FW_IDLE
        LOGGER.info('Flash firmware on Mega: %s', firmware_path)
        ret_val += self.avrdude.flash(firmware_path)
        ret_val += common.wait_tty(self.TTY, LOGGER, timeout=10)
        LOGGER.info("end flash")
        return ret_val

    @logger_call("Reset of mega node")
    def reset(self):
        """ Reset the Mega node using DTR"""
        ret_val = 0
        try:
            ser = serial.Serial(self.TTY, self.BAUDRATE)
            ser.setDTR(False)
            ser.setDTR(True)
        except OSError:
            LOGGER.warning("Nothing to reset")
        ret_val += common.wait_tty(self.TTY, LOGGER, timeout=10)
        return ret_val

    @staticmethod
    def status():
        """ Check Mega node status """
        # It's impossible for us to check the status of the mega node
        return 0
