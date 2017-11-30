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
""" DAPLink commands """

import logging
import os
import shlex
import tempfile

import shutil
from time import sleep

from gateway_code import common
from . import subprocess_timeout


LOGGER = logging.getLogger('gateway_code')


class DapLink(object):
    DEVNULL = open(os.devnull, 'w')

    TIMEOUT = 100

    def __init__(self, config, verb=False, timeout=TIMEOUT):
        self.mount = config['mount']
        self.timeout = timeout

        self.out = None if verb else self.DEVNULL

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

            shutil.copy(hex_path, self.mount)
            LOGGER.info('OK copied hex file to mount')
            os.system('sync')
            LOGGER.info('OK synced the fs before unmount')
            os.system('umount %s' % self.mount)
            LOGGER.info('OK unmounted')

            # removing temporary hex file
            hex_file.close()

            sleep(2)

            return ret_value
        except IOError as err:
            LOGGER.error('%s', err)
            return 1

    def _call_cmd(self, command_str):
        """ Run the given command_str """

        kwargs = self._daplink_args(command_str)
        LOGGER.info(kwargs)

        try:
            return subprocess_timeout.call(timeout=self.timeout, **kwargs)
        except subprocess_timeout.TimeoutExpired as exc:
            LOGGER.error("DapLink '%s' timeout: %s", command_str, exc)
            return 1

    def _daplink_args(self, command_str):
        """ Get subprocess arguments for command_str """
        # Generate full command arguments
        args = shlex.split(command_str)
        return {'args': args, 'stdout': self.out, 'stderr': self.out}
