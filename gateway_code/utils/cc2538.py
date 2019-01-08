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

import logging
import tempfile

from gateway_code import common
from gateway_code.utils.elftarget import get_elf_load_addr
from gateway_code.utils import helpers

LOGGER = logging.getLogger('gateway_code')


class CC2538(object):
    """ Debugger class, implemented as a global variable storage """
    DEVNULL = open(os.devnull, 'w')

    CC2538BSL = ('/usr/bin/cc2538-bsl.py -p {port} {cmd}')

    OBJCOPY = ('objcopy -I elf32-big -O ihex {elf} {hex}')

    RESET = ('')

    FLASH = ('-b {baudrate}'
             ' -e'
             ' -w'
             ' -a 0x{addr:08x}'
             ' -v'
             ' {hex}')

    TIMEOUT = 100

    def __init__(self, config, verb=False, timeout=TIMEOUT):
        self.port = config['port']
        self.baud = config['baudrate']
        self.timeout = timeout

        self.out = None if verb else self.DEVNULL

    def _call_cmd(self, command_str):
        return helpers.call_cmd(command_str,
                                out=self.out, timeout=self.timeout)

    def reset(self):
        """ Reset """
        return self._call_cmd(self.CC2538BSL.format(port=self.port,
                                                    cmd=self.RESET))

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
            ret_value = self._call_cmd(self.OBJCOPY.format(elf=elf_path,
                                                           hex=hex_path))
            LOGGER.info('To hex conversion ret value : %d', ret_value)

            # getting flash addr
            address = get_elf_load_addr(elf_path)

            # Flashing
            flash_cmd = self.FLASH.format(baudrate=self.baud, hex=hex_path,
                                          addr=address)
            ret_value += self._call_cmd(self.CC2538BSL.format(port=self.port,
                                                              cmd=flash_cmd))
            LOGGER.info('Flashing ret value : %d', ret_value)

            # removing temporary hex file
            hex_file.close()

            return ret_value
        except IOError as err:
            LOGGER.error('%s', err)
            return 1
