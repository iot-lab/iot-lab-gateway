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

""" Open Node Leonardo experiment implementation """

import time
import logging

from gateway_code.config import static_path
from gateway_code import common
from gateway_code.common import logger_call
from gateway_code.nodes import OpenNodeBase

from gateway_code.utils.avrdude import AvrDude
from gateway_code.utils.serial_redirection import SerialRedirection

LOGGER = logging.getLogger('gateway_code')


class NodeLeonardo(OpenNodeBase):
    """ Open node Leonardo implementation """

    TYPE = 'leonardo'
    ELF_TARGET = ('ELFCLASS32', 'EM_AVR')
    TTY = '/dev/iotlab/ttyON_LEONARDO'
    # The Leonardo node need a special open/close and then appear on a new TTY
    TTY_PROG = '/dev/ttyON_LEONARDO_PROG'
    # Regular TTY will be restored after 8 seconds
    TTY_RESTORE_TIME = 8 + common.TTY_DETECT_TIME
    TTY_READY_DELAY = 1

    BAUDRATE = 9600
    FW_IDLE = static_path('leonardo_idle.elf')
    FW_AUTOTEST = static_path('leonardo_autotest.elf')
    AVRDUDE_CONF = {
        'tty': TTY_PROG,
        'baudrate': 9600,
        'model': 'atmega32u4',
        'programmer': 'avr109',
        'hex_prefix': '',
        'flash_opts': '-D',
    }

    AUTOTEST_AVAILABLE = [
        'echo', 'get_time',  # mandatory
        'get_uid',
    ]

    ALIM = '5V'

    def __init__(self):
        self.serial_redirection = SerialRedirection(self.TTY, self.BAUDRATE)
        self.avrdude = AvrDude(self.AVRDUDE_CONF)

    @property
    def programmer(self):
        """Returns the avrdude programmer instance of the open node."""
        return self.avrdude

    @logger_call("Node Leonardo : Setup of leonardo node")
    def setup(self, firmware_path):
        """ Flash open node, create serial redirection """
        ret_val = 0

        ret_val += self._wait_tty_ready()
        ret_val += self.flash(firmware_path)
        ret_val += self.serial_redirection.start()
        return ret_val

    @logger_call("Node Leonardo : Teardown of leonardo node")
    def teardown(self):
        """ Stop serial redirection and flash idle firmware """
        ret_val = 0

        ret_val += self._wait_tty_ready()
        ret_val += self.serial_redirection.stop()
        ret_val += self.flash(None)
        return ret_val

    @logger_call("Node Leonardo : Flash of leonardo node")
    def flash(self, firmware_path=None, binary=False, offset=0):
        """ Flash the given firmware on Leonardo node

        :param firmware_path: Path to the firmware to be flashed on `node`.
                              If None, flash 'idle' firmware
        :param binary: whether to flash a binary file
        :param offset: at which offset to flash the binary file """

        if AvrDude.trigger_bootloader(self.TTY, self.TTY_PROG, timeout=15):
            LOGGER.error("FLASH : Leonardo's jtag port not available")
            return 1
        if binary:
            LOGGER.error('FLASH: binary mode not supported with Leonardo')
            return 1
        if offset != 0:
            LOGGER.error('FLASH: flash offset is not supported with Leonardo')
            return 1

        ret_val = 0
        firmware_path = firmware_path or self.FW_IDLE
        LOGGER.info('Flash firmware on Leonardo: %s', firmware_path)
        ret_val += self.avrdude.flash(firmware_path)
        ret_val += common.wait_tty(self.TTY, LOGGER, self.TTY_RESTORE_TIME)
        return ret_val

    @logger_call("Node Leonardo : Reset of leonardo node")
    def reset(self):
        """ Reset the Leonardo node using jtag """
        ret_val = 0
        ret_val += AvrDude.trigger_bootloader(self.TTY, self.TTY_PROG)
        ret_val += common.wait_tty(self.TTY, LOGGER, self.TTY_RESTORE_TIME)
        return ret_val

    @staticmethod
    def status():
        """ Check Leonardo node status """
        # It's impossible for us to check the status of the leonardo node
        return 0

    def _wait_tty_ready(self):
        """Wait that the tty is ready to use.

        Node may have been stopped at the end of the experiment.
        And then restarted again in cn teardown.
        This leads to problem where the TTY disappears and reappears during
        the first 2 seconds. So let some time if it wants to disappear first.

        Also, got some problems when using the tty directly after appearing, so
        git it some delay.
        """
        common.wait_no_tty(self.TTY)
        ret = common.wait_tty(self.TTY, LOGGER)
        # wait tty ready to speak
        time.sleep(self.TTY_READY_DELAY)
        return ret
