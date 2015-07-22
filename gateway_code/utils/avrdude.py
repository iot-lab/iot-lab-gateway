#! /usr/bin/env python
# -*- coding:utf-8 -*-

""" AvrDude commands """

import os
import shlex
import subprocess

import logging
import serial

from gateway_code import common
from gateway_code.common import logger_call
LOGGER = logging.getLogger('gateway_code')


class AvrDude(object):

    """ Debugger class, implemented as a global variable storage """
    DEVNULL = open(os.devnull, 'w')

    AVRDUDE = ('avrdude -C"{cfg}" -v -v -v -v -patmega32u4 -cavr109 -P{tty}'
               ' -b57600 -D'
               ' {cmd}')

    FLASH = (' -Uflash:w:{0}:e')

    def __init__(self, config_file, tty, verb=False):
        self.cfg_file = common.abspath(config_file)
        self.out = None if verb else self.DEVNULL
        self.tty = tty

    @logger_call("AvrDude : flash")
    def flash(self, hex_file):
        """ Flash firmware """
        try:
            hex_path = common.abspath(hex_file)
            return self._call_cmd(self.FLASH.format(hex_path))
        except IOError as err:
            LOGGER.error('%s', err)
            return 1

    def _call_cmd(self, command_str):
        """ Create the subprocess """
        return subprocess.call(**self._avrdude_args(command_str))

    def _avrdude_args(self, command_str):
        """ Get subprocess arguments for command_str """
        # Generate full command arguments
        cmd = self.AVRDUDE.format(
            cfg=self.cfg_file, tty=self.tty, cmd=command_str)
        args = shlex.split(cmd)
        return {'args': args, 'stdout': self.out, 'stderr': self.out}

    @staticmethod
    def trigger_bootloader(tty, tty_prog, timeout=10, baudrate=1200):
        """
        It's impossible to program the Leonardo while still running.
        To be programed the Leonardo has to be in his bootloader sequence.
        While in the bootloader, the Leonardo wait for a new program during 8s
        There are two way to launch the bootloader:
         - The first one physical by pressing the reset button
         - The software way by opening and closing the serial port at 1200bauds
        This method perform the second method.
        """
        try:
            serial.Serial(tty, baudrate).close()
            # Wait the programming interface to be available
            return common.wait_tty(tty_prog, LOGGER, timeout)
        except (OSError, serial.SerialException) as err:
            LOGGER.warning("Error while opening TTY %s: %r", tty, err)
            return 1
