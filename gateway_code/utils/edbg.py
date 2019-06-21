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
""" edbg commands """

# pylint: disable=too-few-public-methods

import os
import shlex

import logging
import tempfile

from gateway_code import common
from . import subprocess_timeout

LOGGER = logging.getLogger('gateway_code')


class Edbg(object):
    """ Debugger class, implemented as a global variable storage """
    DEVNULL = open(os.devnull, 'w')

    EDBG = ('/usr/bin/edbg {cmd}')

    FLASH = (' -t atmel_cm0p'
             ' -b'
             ' -e'
             ' -v'
             ' -p'
             ' -f {bin}')

    TIMEOUT = 100

    def __init__(self, verb=False, timeout=TIMEOUT):
        self.timeout = timeout

        self.out = None if verb else self.DEVNULL

    def flash(self, elf_file):
        """ Flash firmware """
        try:
            ret_value = 0

            elf_path = common.abspath(elf_file)
            LOGGER.info('Creating bin path from %s', elf_path)
            bin_file = tempfile.NamedTemporaryFile(suffix='.bin')
            bin_path = bin_file.name
            LOGGER.info('Created bin path %s', bin_path)

            # creating hex file
            to_bin_command = 'objcopy -I elf32-big -O binary {elf} {bin}'
            cmd = to_bin_command.format(elf=elf_path, bin=bin_path)
            ret_value = self._call_cmd(cmd)
            LOGGER.info('To bin conversion ret value : %d', ret_value)

            # Flashing
            flash_cmd = self.FLASH.format(bin=bin_path)
            cmd = self.EDBG.format(cmd=flash_cmd)
            ret_value += self._call_cmd(cmd)
            LOGGER.info('Flashing ret value : %d', ret_value)

            # removing temporary bin file
            bin_file.close()

            return ret_value
        except IOError as err:
            LOGGER.error('%s', err)
            return 1

    def _call_cmd(self, command_str):
        """ Run the given command_str."""

        kwargs = self._edbg_args(command_str)
        LOGGER.info(kwargs)

        try:
            return subprocess_timeout.call(timeout=self.timeout, **kwargs)
        except subprocess_timeout.TimeoutExpired as exc:
            LOGGER.error("Edbg '%s' timeout: %s", command_str, exc)
            return 1

    def _edbg_args(self, command_str):
        """ Get subprocess arguments for command_str """
        # Generate full command arguments
        args = shlex.split(command_str)
        return dict(args=args, stdout=self.out, stderr=self.out)
