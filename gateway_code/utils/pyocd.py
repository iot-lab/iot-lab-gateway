#! /usr/bin/env python
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


""" pyOCD commands """

import os
import shlex
import subprocess

import atexit

import logging
import tempfile

from gateway_code import common
from . import subprocess_timeout

LOGGER = logging.getLogger('gateway_code')


class PyOCD(object):
    """ Debugger class, implemented as a global variable storage """
    DEVNULL = open(os.devnull, 'w')

    RESET = 'pyocd-tool reset'

    FLASH = 'pyocd-flashtool -ce "{0}"'

    DEBUG = 'pyocd-tool reset -H'
    TIMEOUT = 100

    def __init__(self, verb=False, timeout=TIMEOUT):
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

            LOGGER.info('Creating hex path from %s', elf_path)
            hex_file = tempfile.NamedTemporaryFile(suffix='.hex')
            hex_path = hex_file.name
            LOGGER.info('Created hex path %s', hex_path)

            # creating hex file
            to_hex_command = 'objcopy -I elf32-big -O ihex {elf} {hex}'
            cmd = to_hex_command.format(elf=elf_path, hex=hex_path)
            ret_value = self._call_cmd(cmd)
            LOGGER.info('To hex conversion ret value : %d', ret_value)

            return self._call_cmd(self.FLASH.format(hex_path))
        except IOError as err:
            LOGGER.error('%s', err)
            return 1

    def debug_start(self):
        """ Start a debugger process """
        LOGGER.debug('Debug start')
        self.debug_stop()  # kill previous process
        self._debug = subprocess.Popen(**self._pyocd_args(self.DEBUG))
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
        If pyOCD is in 'debug' mode, return an error """
        if self._debug:
            LOGGER.error("pyOCD is in 'debug' mode, stop it to flash/reset")
            return 1

        kwargs = self._pyocd_args(command_str)
        try:
            return subprocess_timeout.call(timeout=self.timeout, **kwargs)
        except subprocess_timeout.TimeoutExpired as exc:
            LOGGER.error("pyOCD '%s' timeout: %s", command_str, exc)
            return 1

    def _pyocd_args(self, command_str):
        """ Get subprocess arguments for command_str """
        # Generate full command arguments
        args = shlex.split(command_str)
        return {'args': args, 'stdout': self.out, 'stderr': self.out}
