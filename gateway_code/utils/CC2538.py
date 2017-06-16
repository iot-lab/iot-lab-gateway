#! /usr/bin/env python
# -*- coding:utf-8 -*-
""" cc2538 commands """

import os
import shlex
import subprocess

import atexit

import logging

from gateway_code import common
from . import subprocess_timeout

LOGGER = logging.getLogger('gateway_code')


class CC2538(object):
    """ Debugger class, implemented as a global variable storage """
    DEVNULL = open(os.devnull, 'w')


    CC2538BSL = ('/usr/bin/cc2538-bsl.py'
               ' -p {port}'
               ' {cmd}')
    RESET = ('')

    FLASH = ('-b {baudrate}'
             ' -e'
             ' -w'
             ' -a "0x00202000"'
             ' -v'
             ' {hex}'
             )

    DEBUG = ('')

    TIMEOUT = 15


    def __init__(self, config, verb=False, timeout=TIMEOUT):
        self.port = config['port']
        self.baud = config['baudrate']
        self.timeout = timeout

        self.out = None if verb else self.DEVNULL

        self._debug = None
        atexit.register(self.debug_stop)

    def reset(self):
        """ Reset """
        return self._call_cmd(self.RESET)

    def flash(self, elf_file):
        """ Flash firmware """
        try:
            elf_path = common.abspath(elf_file)
            return self._call_cmd(self.FLASH.format(baudrate=self.baud, hex=elf_path))
        except IOError as err:
            LOGGER.error('%s', err)
            return 1
    def debug_start(self):
        """ Start a debugger process """
        LOGGER.debug('Debug start')
        self.debug_stop()  # kill previous process
        self._debug = subprocess.Popen(**self._cc2538_args(self.DEBUG))
        LOGGER.debug('Debug started')
        return 0

    def debug_stop(self):
        """ Stop the debugger process """
        try:
            LOGGER.debug('Debug stop')
            self._debug.terminate()
        except AttributeError:
            LOGGER.debug('Debug not started.')  # None
        except OSError as err:
            LOGGER.error('Debug stop error: %r', err)
            return 1
        finally:
            self._debug = None
            LOGGER.debug('Debug stopped')
        return 0

    def _call_cmd(self, command_str):
        """ Run the given command_str with init on openocd.
        If "CC2538 is in 'debug' mode, return an error """
        if self._debug:
            LOGGER.error("CC2538 is in 'debug' mode, stop it to flash/reset")
            return 1

        kwargs = self._cc2538_args(command_str)
        LOGGER.info(kwargs)

        try:
            return subprocess_timeout.call(timeout=self.timeout, **kwargs)
        except subprocess_timeout.TimeoutExpired as exc:
            LOGGER.error("CC2538 '%s' timeout: %s", command_str, exc)
            return 1

    def _cc2538_args(self, command_str):
        """ Get subprocess arguments for command_str """
        # Generate full command arguments
        cmd = self.CC2538BSL.format(port=self.port, cmd=command_str)
        args = shlex.split(cmd)
        return {'args': args, 'stdout': self.out, 'stderr': self.out}
