# -*- coding:utf-8 -*-
""" Open Node A8 experiment implementation """

from threading import Thread
import time
import datetime

from gateway_code.config import static_path
from gateway_code import common
from gateway_code.common import logger_call

import serial
from gateway_code.utils.serial_expect import SerialExpectForSocket
from gateway_code.utils.serial_redirection import SerialRedirection

import logging
LOGGER = logging.getLogger('gateway_code')


class NodeA8(object):
    """ Open node A8 implementation """

    TYPE = 'a8'
    TTY = '/dev/ttyON_A8'
    BAUDRATE = 115200
    LOCAL_A8_M3_TTY = '/tmp/local_ttyA8_M3'
    A8_M3_TTY = '/dev/ttyA8_M3'
    A8_M3_BAUDRATE = 500000
    A8_M3_FW_AUTOTEST = static_path('a8_autotest.elf')
    ALIM = '5V'

    # 15 secs was not always enough
    A8_TTY_DETECT_TIME = 20

    AUTOTEST_AVAILABLE = [
        'echo', 'get_time',  # mandatory
        'get_uid',
        'get_accelero', 'get_gyro', 'get_magneto',
        'test_gpio', 'test_i2c',
        'radio_pkt', 'radio_ping_pong',
        'test_pps_start', 'test_pps_get', 'test_pps_stop',
        'leds_on', 'leds_off', 'leds_blink',
    ]

    def __init__(self):
        self.serial_redirection = SerialRedirection(self.TTY, self.BAUDRATE)
        self._a8_expect = None

    @logger_call("Node A8 : setup of a8 node")
    def setup(self, _firmware, debug=True):  # pylint: disable=unused-argument
        """ Wait that open nodes tty appears and start A8 boot log """
        ret_val = 0
        common.wait_no_tty(self.TTY)
        ret_val += common.wait_tty(self.TTY, LOGGER, self.A8_TTY_DETECT_TIME)
        ret_val += self.serial_redirection.start()

        if ret_val == 0 and debug:
            # Timeout 15 minutes for boot (we saw 10minutes boot already)
            self._debug_boot_start(15 * 60)
        return ret_val

    @logger_call("Node A8 : teardown of a8 node")
    def teardown(self):
        """ Stop A8 boot log """
        ret_val = 0
        ret_val += self.serial_redirection.stop()
        ret_val += self._debug_boot_stop()
        return ret_val

    def _debug_boot_start(self, timeout):
        """ A8 boot debug thread start """
        thr = Thread(target=self.wait_booted, args=(timeout,))
        thr.daemon = True
        thr.start()

    def wait_booted(self, timeout):
        """ Monitor A8 tty to check if node booted """
        try:
            t_start = time.time()
            LOGGER.debug("Time before boot %s", datetime.datetime.now())
            self._a8_expect = SerialExpectForSocket(logger=LOGGER)
            match = self._a8_expect.expect(' login: ', timeout=timeout)
            LOGGER.debug("Time after boot %s", datetime.datetime.now())
        except (OSError, serial.SerialException) as err:
            LOGGER.warning("Boot monitoring error: %r", err)
            # Happend in tests that tty disappeared between the first
            # 'wait_tty' and serial creation (fast start/stop)
            match = ''
        finally:
            delta_t = time.time() - t_start
            self._debug_boot_stop()

        if match != '':
            LOGGER.info("Boot A8 succeeded in time: %ds", delta_t)
        else:
            LOGGER.error("Boot A8 failed in time: %ds", delta_t)
        return match

    def _debug_boot_stop(self):
        """ Stop the debug thread """
        try:
            self._a8_expect.close()
        except AttributeError:  # pragma: no cover
            pass
        return 0

    @staticmethod
    def status():
        """ Check A8 node status """
        # No check done for the moment
        return 0
