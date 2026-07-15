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


""" ESP tool commands """

import os
import shlex

import logging

from gateway_code import common
from gateway_code.common import logger_call
from . import subprocess_timeout


LOGGER = logging.getLogger('gateway_code')

OFFSET = "0x00000"

class Esp(object):
    """ Debugger class, implemented as a global variable storage """

    _ESP_CONF_KEYS = {'baudrate', 'chip', 'tty'}
    DEVNULL = open(os.devnull, 'w')

    ESPTOOL_FLASH = 'esptool.py --chip {chip} --port {tty} --baud {baudrate} \
               --before default_reset --after hard_reset write_flash \
               -z --flash_mode dio --flash_size detect \
               {cmd}'

    FLASH = '{0} {1}'

    TIMEOUT = 100

    def __init__(self, esp_conf, verb=False, timeout=TIMEOUT):
        assert set(esp_conf.keys()) == self._ESP_CONF_KEYS
        self.timeout = timeout
        self.conf = esp_conf
        self.out = None if verb else self.DEVNULL


    @logger_call("Esptool: flash")
    def flash(self, fw_file, binary=True, offset=0):
        """
            Flash firmware
            TODO return error if using elf instead of bin
        """
        LOGGER.debug("binary: '%s'", binary)
        try:
            path = common.abspath(fw_file)
            if binary is False:
                return self._call_cmd(self.FLASH.format(OFFSET, path))
            else:
                return self._call_cmd(self.FLASH.format(hex(offset), path))
        except IOError as err:
            LOGGER.error('%s', err)
            return 1

    def _call_cmd(self, command_str):
        """ Create the subprocess for flash """
        kwargs = self._esp_args(command_str)
        try:
            return subprocess_timeout.call(timeout=self.timeout,
                                           **kwargs)
        except subprocess_timeout.TimeoutExpired as exc:
            LOGGER.error("esptool flash '%s' timeout: %s", command_str, exc)
            return 1

    def _esp_args(self, command_str):
        """ Get subprocess arguments for command_str """
        # Generate full command arguments
        cmd = self.ESPTOOL_FLASH.format(cmd=command_str, **self.conf)
        args = shlex.split(cmd)
        LOGGER.debug("esptool command: '%s'", cmd)
        return {'args': args, 'stdout': self.out, 'stderr': self.out}
