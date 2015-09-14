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
    _ARVDUDE_CONF_KEYS = {'tty', 'baudrate', 'model', 'programmer'}
    DEVNULL = open(os.devnull, 'w')

    AVRDUDE = 'avrdude -p {model} -P {tty} -c {programmer} -b {baudrate} {cmd}'
    FLASH = ' -D -U {0}'

    def __init__(self, avrdude_conf, verb=False):
        assert set(avrdude_conf.keys()) == self._ARVDUDE_CONF_KEYS
        self.conf = avrdude_conf
        self.out = None if verb else self.DEVNULL

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
        cmd = self.AVRDUDE.format(cmd=command_str, **self.conf)
        args = shlex.split(cmd)
        return {'args': args, 'stdout': self.out, 'stderr': self.out}

    @staticmethod
    def trigger_bootloader(tty, tty_prog, timeout=10, baudrate=1200):
        """ Trigger leonardo bootloader

        To be programed the Leonardo has to be in his bootloader sequence.
        While in the bootloader, the Leonardo wait for a new program during 8s
        There are two way to launch the bootloader:
        - The first one physical by pressing the reset button
        - The software way by opening and closing the serial port at 1200bauds
        This method perform the second method. """
        LOGGER.info("Triggering bootloader")
        try:
            LOGGER.info("Trigerring bootloader")
            serial.Serial(tty, baudrate).close()
            # Wait the programming interface to be available
            return common.wait_tty(tty_prog, LOGGER, timeout)
        except (OSError, serial.SerialException) as err:
            LOGGER.warning("Error while opening TTY %s: %r", tty, err)
            return 1
