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

""" Open Node Raspberry Pi 3 experiment implementation """

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


class NodeRpi3(OpenNodeBase):
    """ Open node RPi3 implementation """

    TYPE = 'rpi3'
    TTY = '/dev/iotlab/ttyON_RPI3'
    BAUDRATE = 115200
    ALIM = '5V'

    # 15 secs was not always enough
    RPI3_TTY_DETECT_TIME = 20

    def __init__(self):
        self.serial_redirection = SerialRedirection(self.TTY, self.BAUDRATE)
        self._rpi3_expect = None

    @property
    def programmer(self):
        """There's no programmer for RPI3 node."""
        return None

    @logger_call("Node RPi3 : setup of rpi3 node")
    def setup(self, _firmware, debug=True):  # pylint: disable=arguments-differ
        """ Wait that open nodes tty appears and start RPi3 boot log """
        ret_val = 0
        common.wait_no_tty(self.TTY)
        ret_val += common.wait_tty(self.TTY, LOGGER, self.RPI3_TTY_DETECT_TIME)
        ret_val += self.serial_redirection.start()

        if ret_val == 0 and debug:
            # Timeout 15 minutes for boot (we saw 10minutes boot already)
            self._debug_boot_start(15 * 60)
        return ret_val

    @logger_call("Node RPi3 : teardown of rpi3 node")
    def teardown(self):
        """ Stop RPi3 boot log """
        ret_val = 0
        ret_val += self.serial_redirection.stop()
        ret_val += self._debug_boot_stop()
        return ret_val

    @classmethod
    def verify(cls):
        # Linux open node = no autotest and firmware target verification
        return 0

    def _debug_boot_start(self, timeout):
        """ RPi3 boot debug thread start """
        thr = Thread(target=self.wait_booted, args=(timeout,))
        thr.daemon = True
        thr.start()

    def wait_booted(self, timeout):
        """ Monitor RPi3 tty to check if node booted """
        t_start = time.time()
        try:
            LOGGER.debug("Time before boot %s", datetime.datetime.now())
            self._rpi3_expect = SerialExpectForSocket(logger=LOGGER)
            match = self._rpi3_expect.expect(' login: ', timeout=timeout)
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
            LOGGER.info("Boot RPi3 succeeded in time: %ds", delta_t)
        else:
            LOGGER.error("Boot RPi3 failed in time: %ds", delta_t)
        return match

    def _debug_boot_stop(self):
        """ Stop the debug thread """
        try:
            self._rpi3_expect.close()
        except AttributeError:  # pragma: no cover
            pass
        return 0

    def status(self):
        """ Check RPi3 node status """
        # No check done for the moment
        return 0
