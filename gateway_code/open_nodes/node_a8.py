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

""" Open Node A8 experiment implementation """

from threading import Thread
import time
import datetime
import logging

import serial

from gateway_code import common
from gateway_code.common import logger_call
from gateway_code.nodes import OpenNodeBase

from gateway_code.utils.serial_expect import SerialExpectForSocket
from gateway_code.utils.serial_redirection import SerialRedirection

LOGGER = logging.getLogger('gateway_code')


class NodeA8(OpenNodeBase):
    """ Open node A8 implementation """

    TYPE = 'a8'
    TTY = '/dev/ttyON_A8'
    BAUDRATE = 115200
    ALIM = '5V'

    # 15 secs was not always enough
    A8_TTY_DETECT_TIME = 20

    def __init__(self):
        self.serial_redirection = SerialRedirection(self.TTY, self.BAUDRATE)
        self._a8_expect = None

    @logger_call("Node A8 : setup of a8 node")
    def setup(self, _firmware, debug=True):  # pylint: disable=arguments-differ
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

    @classmethod
    def verify(cls):
        # Linux open node = no autotest and firmware target verification
        return 0

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

    @staticmethod
    def flash(firmware_path=None, binary=False, offset=None):
        """Flash a firmware on an A8 node.

        This is not supported so does nothing actually."""
        return 0
