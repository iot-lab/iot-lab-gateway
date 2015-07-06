#! /usr/bin/env python
# -*- coding:utf-8 -*-

""" AvrDude commands """

import os
import shlex
import subprocess

import logging
import serial
from serial import SerialException

from gateway_code import common
from gateway_code.common import logger_call
LOGGER = logging.getLogger('gateway_code')


class AvrDude(object):

    """ Debugger class, implemented as a global variable storage """
    DEVNULL = open(os.devnull, 'w')

    AVRDUDE = ('avrdude -C"{cfg}" -v -v -v -v -patmega32u4 -cavr109 -P{tty}'
               ' -b57600 -D'
               ' {cmd}')

    FLASH = (' -Uflash:w:{0}:i')

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

    @classmethod
    @logger_call("AvrDude : trigger the bootloader")
    def trigger_bootloader(cls, tty, tty_prog, timeout=10, baudrate=1200):
        """ Open and close the serial port at 1200 bauds to lauch the soft reset
        of the arduino. Which allow the programming
        """
        try:
            serial.Serial(tty, baudrate).close()
            # Wait the programming interface to be available
            common.wait_tty(tty_prog, LOGGER, timeout)
            return 0
        except SerialException:
            LOGGER.debug(
                "An error occured while triggering Leonardo's bootloader")
            return 1
