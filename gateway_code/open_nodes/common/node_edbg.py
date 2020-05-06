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

""" EDBG based Open Node experiment implementation """
import logging

from gateway_code import common
from gateway_code.common import logger_call
from gateway_code.nodes import OpenNodeBase

from gateway_code.utils.openocd import OpenOCD
from gateway_code.utils.edbg import Edbg
from gateway_code.utils.serial_redirection import SerialRedirection

LOGGER = logging.getLogger('gateway_code')


class NodeEdbgBase(OpenNodeBase):
    # pylint:disable=no-member
    """ Open node EDBG implementation """

    ELF_TARGET = ('ELFCLASS32', 'EM_ARM')
    TTY = '/dev/iotlab/ttyON_CMSIS_DAP'
    BAUDRATE = 115200

    AUTOTEST_AVAILABLE = [
        'echo', 'get_time',  # mandatory
        'get_uid',
        'leds_on', 'leds_off', 'leds_blink'
    ]

    ALIM = '5V'

    def __init__(self):
        self.serial_redirection = SerialRedirection(self.TTY, self.BAUDRATE)
        self.openocd = OpenOCD.from_node(self)
        self.edbg = Edbg()
        self._current_fw = None
        self._in_debug = False

    @property
    def programmer(self):
        """Returns the openocd instance of the open node."""
        return self.edbg

    @logger_call("Node EDBG: Setup of EDBG node")
    def setup(self, firmware_path):
        """ Flash open node, create serial redirection """
        self._in_debug = False
        ret_val = 0

        common.wait_no_tty(self.TTY)
        ret_val += common.wait_tty(self.TTY, LOGGER)
        ret_val += self.flash(firmware_path)
        ret_val += self.serial_redirection.start()
        return ret_val

    @logger_call("Node EDBG: teardown of EDBG node")
    def teardown(self):
        """ Stop serial redirection and flash idle firmware """
        self._in_debug = False
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

    @logger_call("Node EDBG: flash of edbg node")
    def flash(self, firmware_path=None, binary=False, offset=0):
        """ Flash the given firmware on EDBG node

        :param firmware_path: Path to the firmware to be flashed on `node`.
                              If None, flash 'idle' firmware.
        """
        firmware_path = firmware_path or self.FW_IDLE
        LOGGER.info('Flash firmware on %s: %s',
                    self.TYPE.upper(), firmware_path)
        self._current_fw = firmware_path

        if self._in_debug:
            return self.openocd.flash(firmware_path, binary, offset)

        return self.edbg.flash(firmware_path, binary, offset)

    @logger_call("Node EDBG: reset of EDBG node")
    def reset(self):
        """ Reset the EDBG node using jtag """
        LOGGER.info('Reset %s node', self.TYPE.upper())
        return self.openocd.reset()

    def debug_start(self):
        """ Start EDBG node debugger """
        LOGGER.info('%s Node debugger start', self.TYPE.upper())
        self._in_debug = True
        if self._current_fw is not None:
            # Reflash current firmware using openocd to avoid misbehavior of
            # previously flashed firmware (with edbg)
            self.flash(firmware_path=self._current_fw)
        return self.openocd.debug_start()

    def debug_stop(self):
        """ Stop EDBG node debugger """
        LOGGER.info('%s Node debugger stop', self.TYPE.upper())
        self._in_debug = False
        return self.openocd.debug_stop()

    @staticmethod
    def status():
        """ Check EDBG node status """
        # Status is called when open node is not powered
        # So can't check for FTDI
        return 0
