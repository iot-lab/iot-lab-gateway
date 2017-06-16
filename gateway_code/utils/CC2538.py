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
""" cc2538 commands """

import os
import shlex
import subprocess

import atexit

import logging
import tempfile

from gateway_code import common
from gateway_code.utils.elftarget import get_elf_load_addr
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
             ' -a 0x{addr:08x}'
             ' -v'
             ' {hex}')

    DEBUG = ('')

    TIMEOUT = 100

    def __init__(self, config, verb=False, timeout=TIMEOUT):
        self.port = config['port']
        self.baud = config['baudrate']
        self.timeout = timeout

        self.out = None if verb else self.DEVNULL

        self._debug = None
        atexit.register(self.debug_stop)

    def reset(self):
        """ Reset """
        cmd = self.CC2538BSL.format(port=self.port, cmd=self.RESET)
        return self._call_cmd(cmd)

    def flash(self, elf_file):
        """ Flash firmware """
        try:
            ret_value = 0

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

            # getting flash addr
            address = get_elf_load_addr(elf_path)

            # Flashing
            flash_cmd = self.FLASH.format(baudrate=self.baud, hex=hex_path,
                                          addr=address, elf=elf_path)
            cmd = self.CC2538BSL.format(port=self.port, cmd=flash_cmd)
            ret_value += self._call_cmd(cmd)
            LOGGER.info('Flashing ret value : %d', ret_value)

            # removing temporary hex file
            hex_file.close()

            return ret_value
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
        args = shlex.split(command_str)
        return {'args': args, 'stdout': self.out, 'stderr': self.out}
