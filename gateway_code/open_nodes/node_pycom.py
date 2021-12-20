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

""" Open Node Pycom experiment implementation """

import os.path
import time
import logging
import shlex
import serial

import gateway_code.common
from gateway_code.common import logger_call
from gateway_code.utils.serial_redirection import SerialRedirection
from gateway_code.open_nodes.common.node_no import NodeNoBase
from gateway_code import config
from gateway_code.utils import subprocess_timeout

LOGGER = logging.getLogger('gateway_code')
PYCOM_SAFE_REBOOT_SEQUENCE = {
    b"\x03\r\n",  # Interrupt any running code
    b"\x06\r\n",  # Perform safe boot with Ctrl + F
}
PYCOM_FLASH_ERASE_SEQUENCE = (
    b"import os\r\n",
    b"os.fsformat('/flash')\r\n",  # Erase the flash
)
PYCOM_RESET_SEQUENCE = (
    b"import machine\r\n",
    b"machine.reset()\r\n",
)

PYCOM_UPDATE_BIN = "sudo /usr/bin/python3 /usr/local/share/pycom/eps32/tools/fw_updater/updater.py"
PYCOM_FLASH_ERASE_HARD = "{bin} --pic -p {port} erase_fs"

LOCAL_CONFIG_DIR = '/var/local/config'
FULL_ARCHI_CONFIG = os.path.join(LOCAL_CONFIG_DIR, 'archi')


def _call_cmd(command_str):
    """ Run the given command_str."""

    kwargs = {'args': shlex.split(command_str)}
    try:
        return subprocess_timeout.call(**kwargs)
    except subprocess_timeout.TimeoutExpired as exc:
        LOGGER.error("Command '%s' timeout: %s", command_str, exc)
        return 1

class NodePycom(NodeNoBase):
    """ Open node Pycom implementation """

    TYPE = 'pycom'
    TTY = '/dev/iotlab/ttyON_PYCOM'
    BAUDRATE = 115200

    def __init__(self):
        self.expansion_board = False
        self.serial_redirection = SerialRedirection(
            self.TTY, self.BAUDRATE, serial_opts=('echo=0', 'raw', 'crnl'))
        if os.path.isfile(FULL_ARCHI_CONFIG):
            archi = config.read_config('archi')
            LOGGER.debug("Node Pycom: archi %s", archi)
            self.archi = archi
            if 'eb31' in archi:
                LOGGER.info("Node Pycom: Expansion Board configured")
                self.expansion_board = True

    def _send_sequence(self, sequence, delay=None):
        try:
            ser = serial.Serial(self.TTY, self.BAUDRATE)
        except serial.serialutil.SerialException:
            LOGGER.error("No serial port found")
            return 1
        else:
            for command in sequence:
                ser.write(command)
                if delay is not None:
                    time.sleep(delay)
                LOGGER.info("%s: %s", command, ser.read_all())
            ser.close()
        return 0

    @logger_call("Node Pycom: Setup node")
    def setup(self, firmware_path=None):
        """Start the custom serial redirection.
        Access from the frontend:
            socat -,echo=0 tcp:<node>:20000
        Access from pymakr:
            ssh -L 20000:<pycom node>:20000 <login>@<site>.iot-lab.info
            socat PTY,link=/tmp/ttyS0,echo=0,crnl TCP:localhost:20000
        """
        if self.expansion_board is True:
            ret_val = _call_cmd(PYCOM_FLASH_ERASE_HARD.format(bin=PYCOM_UPDATE_BIN, port=self.TTY))
        ret_val += gateway_code.common.wait_tty(self.TTY, LOGGER, timeout=10)
        ret_val += self._send_sequence(PYCOM_SAFE_REBOOT_SEQUENCE, delay=2)
        ret_val += self._send_sequence(PYCOM_FLASH_ERASE_SEQUENCE)
        ret_val += self.reset()
        ret_val += self.serial_redirection.start()
        return ret_val

    @logger_call("Node Pycom: teardown node")
    def teardown(self):
        """Stop the serial redirection."""
        ret_val = self._send_sequence(PYCOM_SAFE_REBOOT_SEQUENCE, delay=2)
        ret_val += self._send_sequence(PYCOM_FLASH_ERASE_SEQUENCE)
        ret_val += self.serial_redirection.stop()
        if self.expansion_board is True:
            ret_val += _call_cmd(PYCOM_FLASH_ERASE_HARD.format(bin=PYCOM_UPDATE_BIN, port=self.TTY))
        return ret_val

    @logger_call("Node Pycom: reset node")
    def reset(self):
        """Machine reset of the pycom node."""
        return self._send_sequence(PYCOM_RESET_SEQUENCE)
