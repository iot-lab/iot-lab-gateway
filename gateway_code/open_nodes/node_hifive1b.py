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

""" Open Node SiFive HiFive1b experiment implementation """

import logging
import time

from gateway_code import common
from gateway_code.common import logger_call
from gateway_code.config import static_path
from gateway_code.open_nodes.common.node_openocd import NodeOpenOCDBase

LOGGER = logging.getLogger('gateway_code')


class NodeHifive1b(NodeOpenOCDBase):
    """ Open node SiFive HiFive1b implementation """

    ELF_TARGET = ('ELFCLASS32', 243)
    TYPE = 'hifive1b'
    OPENOCD_CFG_FILE = static_path('iot-lab-hifive1b.cfg')
    OPENOCD_PATH = '/opt/openocd-dev/bin/openocd'
    OPENOCD_NO_MONITOR = True
    FW_IDLE = static_path('hifive1b_idle.elf')
    FW_AUTOTEST = static_path('hifive1b_autotest.elf')
    TTY = '/dev/iotlab/ttyON_HIFIVE1B'
    BAUDRATE = 115200

    @logger_call("Node Hifive1b: Setup of hifive1b node")
    def setup(self, firmware_path):
        """ Flash open node, create serial redirection """
        # This board takes a little less than 1s to boot and cannot be flashed
        # during that time.
        time.sleep(1)
        ret_val = 0
        common.wait_no_tty(self.TTY)
        ret_val += common.wait_tty(self.TTY, LOGGER)
        ret_val += self.flash(firmware_path)
        ret_val += self.serial_redirection.start()
        return ret_val

    @logger_call("Node Hifive1b: flash of hifive1b node")
    def flash(self, firmware_path=None, binary=False, offset=0):
        """ Flash the given firmware on hifive1b node

        :param firmware_path: Path to the firmware to be flashed on `node`.
                              If None, flash 'idle' firmware.
        :param binary: if True, flashes a binary file
        :param offset: the offset at which to flash the binary file
        """
        if binary:
            LOGGER.error('FLASH: binary mode not supported with hifive1b')
            return 1

        if offset != 0:
            LOGGER.error('FLASH: flash offset is not supported with hifive1b')
            return 1

        firmware_path = firmware_path or self.FW_IDLE
        LOGGER.info('Flash firmware on Hifive1b: %s', firmware_path)
        ret_val = self.openocd.flash(firmware_path, binary, offset)
        return ret_val
