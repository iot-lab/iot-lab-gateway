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


""" OpenOCD commands """

import os
import shlex
import subprocess

import atexit

import logging

from gateway_code import common
from . import subprocess_timeout

LOGGER = logging.getLogger('gateway_code')


class OpenOCD(object):
    """ Debugger class, implemented as a global variable storage """
    DEVNULL = open(os.devnull, 'w')

    OPENOCD = ('openocd --debug=0'
               ' {config}'
               ' -c "init"'
               ' -c "targets"'
               ' {cmd}')

    RESET = (' -c "reset run"'
             ' -c "shutdown"')

    FLASH = (' -c "reset halt"'
             ' -c "reset init"'
             ' -c "flash write_image erase {0}"'
             ' -c "verify_image {0}"'
             ' -c "reset run"'
             ' -c "shutdown"')

    DEBUG = ' -c "reset halt"'
    TIMEOUT = 100

    def __init__(self, config_file, opts=(), verb=False, timeout=TIMEOUT):
        self.config = self._config(config_file, opts)
        self.timeout = timeout

        self.out = None if verb else self.DEVNULL

        self._debug = None
        atexit.register(self.debug_stop)

    @staticmethod
    def _config(config_file, opts=()):
        """Return config options for `config_file` and `opts`.

        >>> OpenOCD._config('/dev/null')
        '-f "/dev/null"'

        >>> OpenOCD._config('/dev/null', ['target/stm32.cfg'])
        '-f "/dev/null" -f "target/stm32.cfg"'

        # Abspath
        >>> OpenOCD._config('gateway_code/static/iot-lab-m3.cfg')
        ... # doctest: +ELLIPSIS
        '-f "/.../gateway_code/static/iot-lab-m3.cfg"'
        """
        cfg_file = common.abspath(config_file)
        opts = [cfg_file] + list(opts)
        opts = ('-f "%s"' % opt for opt in opts)
        return ' '.join(opts)

    def reset(self):
        """ Reset """
        return self._call_cmd(self.RESET)

    def flash(self, elf_file):
        """ Flash firmware """
        try:
            elf_path = common.abspath(elf_file)
            return self._call_cmd(self.FLASH.format(elf_path))
        except IOError as err:
            LOGGER.error('%s', err)
            return 1

    def debug_start(self):
        """ Start a debugger process """
        LOGGER.debug('Debug start')
        self.debug_stop()  # kill previous process
        self._debug = subprocess.Popen(**self._openocd_args(self.DEBUG))
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
        If openocd is in 'debug' mode, return an error """
        if self._debug:
            LOGGER.error("OpenOCD is in 'debug' mode, stop it to flash/reset")
            return 1

        kwargs = self._openocd_args(command_str)
        try:
            return subprocess_timeout.call(timeout=self.timeout, **kwargs)
        except subprocess_timeout.TimeoutExpired as exc:
            LOGGER.error("Openocd '%s' timeout: %s", command_str, exc)
            return 1

    def _openocd_args(self, command_str):
        """ Get subprocess arguments for command_str """
        # Generate full command arguments
        cmd = self.OPENOCD.format(config=self.config, cmd=command_str)
        args = shlex.split(cmd)
        return {'args': args, 'stdout': self.out, 'stderr': self.out}

    @classmethod
    def from_node(cls, nodeclass, *args, **kwargs):
        """Return an instance of OpenOCD configured for node.

        * nodeclass.OPENOCD_CFG_FILE configuration file
        * nodeclass.OPENOCD_OPTS iterable telling other config options
             They will be added after configuration file with '-f'
        """
        return cls(nodeclass.OPENOCD_CFG_FILE, nodeclass.OPENOCD_OPTS,
                   *args, **kwargs)
