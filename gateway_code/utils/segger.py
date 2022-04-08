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


""" Segger commands """

import os
import shlex
import subprocess

import atexit

import logging
import tempfile

from collections import namedtuple

from gateway_code import common
from . import subprocess_timeout

LOGGER = logging.getLogger('gateway_code')

JLinkSeggerArgs = namedtuple("JLinkSeggerArgs", ['path', 'opts', 'serial',
                                                 'reset_file', 'flash_addr', 'itf', 'device' ])

# default GDB port
GDB_PORT = 3333
# default telnet port
TELNET_PORT = 4444
# default J-Link command names, interface and speed
JLINK_PATH = "/usr/local/share/JLink"
JLINK = "JLinkExe"
JLINK_SERVER = "JLinkGDBServer"
JLINK_SPEED = 2000
JLINK_CMDFILE_FLASH = "/tmp/burn.seg"

class Segger:
    """ Debugger class, implemented as a global variable storage """
    DEVNULL = open(os.devnull, 'w')

    JLINKEXE_CMD = ('{jlink_path}' + '/' + JLINK +
                    ' {jlink_serial}'
                    ' {cmd}')

    FLASH = (' -nogui 1'
             ' -exitonerror 1'
             ' -device "{jlink_device}"'
             ' -speed "{jlink_speed}"'
             ' -if "{jlink_itf}"'
             ' -jtagconf -1,-1'
             ' -commandfile "{cmdfile}"')

    JLINKSERVER_CMD = ('{jlink_path}' + '/' + JLINK_SERVER +
                    ' {jlink_serial}'
                    ' {cmd}')

    DEBUG = (' -nogui 1'
             ' -silent'
             ' -device "{jlink_device}"'
             ' -speed "{jlink_speed}"'
             ' -if "{jlink_itf}"'
             ' -port "{gdb_port}"'
             ' -telnetport "{telnet_port}"')


    TIMEOUT = 100

    def __init__(self, segger_args,
                 verb=False, timeout=TIMEOUT):
        self.segger_args = segger_args
        self.jlink_path = self.segger_args.path
        self.jlink_serial = self.segger_args.serial
        self.jlink_flash_addr = self.segger_args.flash_addr
        self.jlink_device = self.segger_args.device
        self.jlink_itf = self.segger_args.itf
        self.timeout = timeout
        self.out = None if verb else self.DEVNULL

        self._debug = None
        atexit.register(self.debug_stop)

    def reset(self):
        """ Reset """
        _cmd = self.FLASH.format(jlink_device=self.jlink_device,
                                jlink_speed=JLINK_SPEED,
                                jlink_itf=self.jlink_itf,
                                cmdfile=self.segger_args.reset_file)
        return self._call_cmd_flash(_cmd)

    def flash(self, fw_file, binary=False, offset=0):
        """ Flash firmware """
        try:
            fw_path = common.abspath(fw_file)
            if not binary:
                LOGGER.info('Creating bin file from %s', fw_path)
                bin_file = tempfile.NamedTemporaryFile(suffix='.bin')
                bin_path = bin_file.name
                LOGGER.info('Created bin file in %s', bin_path)

                # creating hex file
                to_bin_command = 'objcopy -I elf32-big -O binary {elf} {bin}'
                cmd = to_bin_command.format(elf=fw_path, bin=bin_path)
                ret_value = self._call_cmd(cmd)
                LOGGER.info('To bin conversion ret value : %d', ret_value)
                fw_path = bin_path
                # Ensure offset is 0 with elf firmware
                offset = 0

            self._commandline_file(fw_path, offset)
            _cmd = self.FLASH.format(jlink_device=self.jlink_device,
                                    jlink_speed=JLINK_SPEED,
                                    jlink_itf=self.jlink_itf,
                                    cmdfile=JLINK_CMDFILE_FLASH)
            LOGGER.info("FLASH: %s", _cmd)
            return self._call_cmd_flash(_cmd)
        except IOError as err:
            LOGGER.error('%s', err)
            return 1

    def _call_cmd(self, command_str):
        """ Run the given command_str."""
        kwargs = self._cmd_args(command_str)
        LOGGER.info(kwargs)
        try:
            return subprocess_timeout.call(timeout=self.timeout, **kwargs)
        except subprocess_timeout.TimeoutExpired as exc:
            LOGGER.error("Edbg '%s' timeout: %s", command_str, exc)
            return 1

    def _cmd_args(self, command_str):
        """ Get subprocess arguments for command_str """
        # Generate full command arguments
        args = shlex.split(command_str)
        return dict(args=args, stdout=self.out, stderr=self.out)

    def _commandline_file(self, fw_path, offset=0):
        """ Generate JLinkExe batch commands file """
        # opening first file in append mode and second file in read mode
        f_reset = open(self.segger_args.reset_file, 'r')
        flash_addr = hex(self.jlink_flash_addr + offset)
        with open(JLINK_CMDFILE_FLASH, 'w') as f_burn:
            f_burn.write(f"loadbin {fw_path} {flash_addr}\n")
            f_burn.write(f_reset.read())

    def _call_cmd_flash(self, command_str):
        """
            Run the given command_str with init on openocd.
            If Segger is in 'debug' mode, return an error
        """
        if self._debug:
            LOGGER.error("Segger is in 'debug' mode, stop it to flash/reset")
            return 1

        kwargs = self._segger_args_jlinkexe(command_str)
        LOGGER.info("FLASH KWARGS: %s", kwargs)
        try:
            return subprocess_timeout.call(timeout=self.timeout, **kwargs)
        except subprocess_timeout.TimeoutExpired as exc:
            LOGGER.error("Segger '%s' timeout: %s", command_str, exc)
            return 1

    def _segger_args_jlinkexe(self, command_str):
        """ Get jlinkexe subprocess arguments for command_str """
        # Generate full command arguments
        serial_arg = ""
        if self.jlink_serial != "":
            serial_arg = f" -selectemubysn {self.jlink_serial}"
        cmd = self.JLINKEXE_CMD.format(jlink_path=self.jlink_path,
                                       jlink_serial=serial_arg,
                                       cmd=command_str)
        args = shlex.split(cmd)
        return {'args': args, 'stdout': self.out, 'stderr': self.out}

    def debug_start(self):
        """ Start a debugger process """
        LOGGER.debug('Debug start')

        _cmd = self.DEBUG.format(jlink_device=self.jlink_device,
                                jlink_speed=JLINK_SPEED,
                                jlink_itf=self.jlink_itf,
                                gdb_port=GDB_PORT,
                                telnet_port=TELNET_PORT)
        LOGGER.info("DEBUG: %s", _cmd)
        self.debug_stop()  # kill previous process
        self._debug = subprocess.Popen(**self._segger_args_jlinkgdbserver(_cmd))
        LOGGER.debug('Debug started')
        return 0

    def _call_cmd_debug(self, command_str):
        """
            Run the given command_str with init on openocd.
            If Segger is in 'debug' mode, return an error
        """
        if self._debug:
            LOGGER.error("Segger is in 'debug' mode, stop it to flash/reset")
            return 1

        kwargs = self._segger_args_jlinkexe(command_str)
        LOGGER.info("FLASH KWARGS: %s", kwargs)
        try:
            return subprocess_timeout.call(timeout=self.timeout, **kwargs)
        except subprocess_timeout.TimeoutExpired as exc:
            LOGGER.error("Segger '%s' timeout: %s", command_str, exc)
            return 1

    def _segger_args_jlinkgdbserver(self, command_str):
        """ Get jlinkgdbserver subprocess arguments for command_str """
        # Generate full command arguments
        serial_server_arg = ""
        if self.jlink_serial != "":
            serial_server_arg = f"-select usb='{self.jlink_serial}'"
        cmd = self.JLINKSERVER_CMD.format(jlink_path=self.jlink_path,
                                       jlink_serial=serial_server_arg,
                                       cmd=command_str)
        args = shlex.split(cmd)
        return {'args': args, 'stdout': self.out, 'stderr': self.out}

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

    @classmethod
    def from_node(cls, nodeclass, *args, **kwargs):
        """ Return an instance of JLINK configured for node.

            * nodeclass.JLINK_PATH_PATH: jlink command full path (optional)
            * nodeclass.JLINK_OPTS: iterable telling other config options
              (optional)
            * nodeclass.JLINK_SERIAL: JLink unique id for handling multiple nodes
              (optional)

            NOTE: JLINK_SERIAL should be move as config resource
        """
        if not hasattr(nodeclass, "JLINK_PATH"):
            nodeclass.JLINK_PATH = JLINK_PATH
        if not hasattr(nodeclass, "JLINK_OPTS"):
            nodeclass.JLINK_OPTS = ()
        if not hasattr(nodeclass, "JLINK_SERIAL"):
            nodeclass.JLINK_SERIAL = ""

        return cls(JLinkSeggerArgs(nodeclass.JLINK_PATH,
                               nodeclass.JLINK_OPTS,
                               nodeclass.JLINK_SERIAL,
                               nodeclass.JLINK_RESET_FILE,
                               nodeclass.JLINK_FLASH_ADDR,
                               nodeclass.JLINK_IF,
                               nodeclass.JLINK_DEVICE),
                   *args, **kwargs)
