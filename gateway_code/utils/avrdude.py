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


""" AvrDude commands """

import os
import shlex

import logging
import serial

from gateway_code import common
from gateway_code.common import logger_call
from . import subprocess_timeout

LOGGER = logging.getLogger('gateway_code')


class AvrDude(object):
    """ Debugger class, implemented as a global variable storage """
    _ARVDUDE_CONF_KEYS = {
        'tty', 'baudrate', 'model', 'programmer', 'hex_prefix', 'flash_opts'
    }
    DEVNULL = open(os.devnull, 'w')

    AVRDUDE_TTY_CONF = '-P {tty} -b {baudrate}'
    AVRDUDE_PROG_CONF = '-p {model} -c {programmer}'
    AVRDUDE = 'avrdude {prog_conf} {tty_conf} {cmd}'
    FLASH = ' {flash_opts} -U {hex_prefix}{hex_path}'

    TIMEOUT = 100

    def __init__(self, avrdude_conf, verb=False, timeout=TIMEOUT):
        assert set(avrdude_conf.keys()) == self._ARVDUDE_CONF_KEYS
        self.timeout = timeout
        self.conf = avrdude_conf
        self.out = None if verb else self.DEVNULL

    @logger_call("AvrDude : flash")
    def flash(self, hex_file):
        """ Flash firmware """
        try:
            hex_path = common.abspath(hex_file)
            return self._call_cmd(self.FLASH.format(
                hex_path=hex_path,
                **self.conf
            ))
        except IOError as err:
            LOGGER.error('%s', err)
            return 1

    @logger_call("AvrDude : reset")
    def reset(self):
        """Reset board: just call avrdude with an empty command."""
        return self._call_cmd('')

    def _call_cmd(self, command_str):
        """ Create the subprocess """
        kwargs = self._avrdude_args(command_str)
        try:
            return subprocess_timeout.call(timeout=self.timeout, **kwargs)
        except subprocess_timeout.TimeoutExpired as exc:
            LOGGER.error("Openocd '%s' timeout: %s", command_str, exc)
            return 1

    def _avrdude_args(self, command_str):
        """ Get subprocess arguments for command_str """
        # Generate full command arguments
        if self.conf['tty'] is not None:
            tty_conf = self.AVRDUDE_TTY_CONF.format(**self.conf)
        else:
            tty_conf = ''
        prog_conf = self.AVRDUDE_PROG_CONF.format(**self.conf)

        cmd = self.AVRDUDE.format(
            cmd=command_str, tty_conf=tty_conf, prog_conf=prog_conf
        )
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
