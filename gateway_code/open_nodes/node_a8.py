# -*- coding:utf-8 -*-
""" Open Node A8 experiment implementation """

from threading import Thread
import time

from gateway_code.config import static_path
from gateway_code import common
from gateway_code.common import logger_call

from gateway_code.utils.serial_expect import SerialExpect

import logging
LOGGER = logging.getLogger('gateway_code')


class NodeA8(object):

    """ Open node A8 implementation """
    TTY = '/dev/ttyON_A8'
    BAUDRATE = 115200
    LOCAL_A8_M3_TTY = '/tmp/local_ttyA8_M3'
    A8_M3_TTY = '/dev/ttyA8_M3'
    A8_M3_BAUDRATE = 500000
    A8_M3_FW_AUTOTEST = static_path('a8_autotest.elf')
    ALIM = '5V'

    # 15 secs was not always enough
    A8_TTY_DETECT_TIME = 20

    AUTOTEST_ANSWERS = ['check_get_time',
                        'get_uid',
                        'test_gyro',
                        'test_magneto',
                        'test_accelero',
                        'test_gpio',
                        'test_i2c',
                        'test_radio_ping_pong',
                        'test_radio_with_rssi',
                        'test_consumption_dc',
                        'test_gps',
                        'test_consumption_batt',
                        ]

    def __init__(self):
        self._a8_expect = None

    @logger_call("Node A8 : setup of a8 node")
    def setup(self, firmware_path):  # pylint: disable=unused-argument
        """ Wait that open nodes tty appears and start A8 boot log """
        ret = common.wait_tty(self.TTY, LOGGER, self.A8_TTY_DETECT_TIME)
        if ret == 0:
            # Timeout 15 minutes for boot (we saw 10minutes boot already)
            self._debug_boot_start(15 * 60)
        return ret

    @logger_call("Node A8 : teardown of a8 node")
    def teardown(self):
        """ Stop A8 boot log """
        self._debug_boot_stop()
        return 0

    def _debug_boot_start(self, timeout):
        """ A8 boot debug thread start """
        thr = Thread(target=self._debug_thread, args=(timeout,))
        thr.daemon = True
        thr.start()

    def _debug_thread(self, timeout):
        """ Monitor A8 tty to check if node booted """
        t_start = time.time()
        try:
            self._a8_expect = SerialExpect(self.TTY, self.BAUDRATE, LOGGER)
            match = self._a8_expect.expect(' login: ', timeout=timeout)
        except OSError:
            # Happend in tests that tty disappeared between the first
            # 'wait_tty' and serial creation (fast start/stop)
            match = ''
        delta_t = time.time() - t_start

        if match != '':
            LOGGER.info("Boot A8 succeeded in time: %ds", delta_t)
        else:
            LOGGER.error("Boot A8 failed in time: %ds", delta_t)
        return match

    def _debug_boot_stop(self):
        """ Stop the debug thread """
        try:
            self._a8_expect.serial_fd.close()
        except AttributeError:  # pragma: no cover
            pass

    @staticmethod
    def status():
        """ Check A8 node status """
        # No check done for the moment
        return 0
