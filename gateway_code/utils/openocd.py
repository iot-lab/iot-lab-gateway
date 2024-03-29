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
from collections import namedtuple

from gateway_code import common
from . import subprocess_timeout

LOGGER = logging.getLogger('gateway_code')

OpenOCDArgs = namedtuple(
    "OpenOCDArgs",
    [
        'path',
        'config_file',
        'opts',
        'bind_ip',
        'serial_number',
        'serial_cmd',
    ]
)


class OpenOCD:   # pylint:disable=too-many-instance-attributes
    """ Debugger class, implemented as a global variable storage """
    DEVNULL = open(os.devnull, 'w')

    OPENOCD = (
        '{openocd_path} --debug=0'
        ' {config}'
        ' {serial_cmd}'
        ' -c "bindto {bind_ip}"'
        ' -c "init"'
        ' -c "targets"'
        ' {cmd}'
    )

    RESET = (
        ' -c "reset run"'
        ' -c "shutdown"'
    )

    FLASH = (
        ' -c "reset halt"'
        ' -c "reset init"'
        ' -c "flash write_image erase {firmware}"'
        ' -c "verify_image {firmware}"'
        ' -c "reset run"'
        ' -c "shutdown"'
    )

    FLASH_BIN = (
        ' -c "reset halt"'
        ' -c "reset init"'
        ' -c "program {firmware} verify {offset}"'
        ' -c "reset run"'
        ' -c "shutdown"'
    )

    DEBUG = (
        ' -c "reset halt"'
    )
    TIMEOUT = 100

    def __init__(self, openocd_args,
                 verb=False, timeout=TIMEOUT):
        self.openocd_path = openocd_args.path
        self.config = self._config(openocd_args.config_file, openocd_args.opts)
        self.timeout = timeout
        self.bind_ip = openocd_args.bind_ip

        # Compute the serial_cmd string. Empty if no serial number or cmd is
        # available.
        self.serial_cmd = ""
        if (
            openocd_args.serial_cmd is not None and
            openocd_args.serial_number is not None
        ):
            self.serial_cmd = openocd_args.serial_cmd.format(
                serial=openocd_args.serial_number
            )

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
        >>> OpenOCD._config('gateway_code/static/iot-lab.cfg')
        ... # doctest: +ELLIPSIS
        '-f "/.../gateway_code/static/iot-lab.cfg"'
        """
        cfg_file = common.abspath(config_file)
        opts = [cfg_file] + list(opts)
        return ' '.join((f'-f "{opt}"' for opt in opts))

    def reset(self):
        """ Reset """
        return self._call_cmd(self.RESET)

    def flash(self, fw_file, binary=False, offset=0):
        """ Flash firmware """
        try:
            path = common.abspath(fw_file)
            if binary:
                return self._call_cmd(
                    self.FLASH_BIN.format(
                        firmware=path,
                        offset=hex(offset)
                    )
                )
            return self._call_cmd(self.FLASH.format(firmware=path))
        except IOError as err:
            LOGGER.error('%s', err)
            return 1

    def debug_start(self):
        """ Start a debugger process """
        LOGGER.debug('Debug start')
        self.debug_stop()  # kill previous process
        self._debug = subprocess.Popen(
            **self._openocd_args(self.DEBUG)
        )
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
        cmd = self.OPENOCD.format(
            openocd_path=self.openocd_path,
            serial_cmd=self.serial_cmd,
            config=self.config,
            bind_ip=self.bind_ip,
            cmd=command_str
        )
        args = shlex.split(cmd)
        return {'args': args, 'stdout': self.out, 'stderr': self.out}

    @classmethod
    def from_node(cls, nodeclass, *args, **kwargs):
        """Return an instance of OpenOCD configured for node.

        * nodeclass.OPENOCD_CFG_FILE configuration file
        * nodeclass.OPENOCD_PATH: openocd command full path (optional)
        * nodeclass.OPENOCD_OPTS iterable telling other config options
          (optional) They will be added after configuration file with '-f'
        """
        if not hasattr(nodeclass, "OPENOCD_PATH"):
            nodeclass.OPENOCD_PATH = "openocd"
        if not hasattr(nodeclass, "OPENOCD_OPTS"):
            nodeclass.OPENOCD_OPTS = ()
        if not hasattr(nodeclass, "BIND_IP"):
            # Debugger listens to any addresses by default
            nodeclass.BIND_IP = "0.0.0.0"
        if not hasattr(nodeclass, "OPENOCD_SERIAL_NUMBER"):
            # No serial number provided by default => can only work with a
            # single board per gateway
            nodeclass.OPENOCD_SERIAL_NUMBER = None
        if not hasattr(nodeclass, "OPENOCD_SERIAL_CMD"):
            nodeclass.OPENOCD_SERIAL_CMD = None

        return cls(
            OpenOCDArgs(
                nodeclass.OPENOCD_PATH,
                nodeclass.OPENOCD_CFG_FILE,
                nodeclass.OPENOCD_OPTS,
                nodeclass.BIND_IP,
                nodeclass.OPENOCD_SERIAL_NUMBER,
                nodeclass.OPENOCD_SERIAL_CMD,
            ), *args, **kwargs
        )
