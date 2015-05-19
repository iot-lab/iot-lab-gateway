#! /usr/bin/env python
# -*- coding:utf-8 -*-


"""
OpenOCD commands
"""

import shlex
import subprocess
import atexit

import os

import logging
LOGGER = logging.getLogger('gateway_code')


OPENOCD_BASE_CMD = '''
    openocd --debug=0
        -f "{0}"
        -f "target/stm32f1x.cfg"
        -c "init"
        -c "targets"
        '''

RESET_CMD = '''
        -c "reset run"
        -c "shutdown"
'''
FLASH_CMD = '''
        -c "reset halt"
        -c "reset init"
        -c "flash write_image erase {0}"
        -c "verify_image {0}"
        -c "reset run"
        -c "shutdown"
'''
DEBUG_CMD = '-c "reset halt"'


def reset(config_file, verb=False):
    """ Reset """
    return OpenOCD.call_cmd(config_file, RESET_CMD, verb)


def flash(config_file, elf_file, verb=False):
    """ Flash firmware """
    try:
        # get the absolute file path required for openocd
        elf_path = os.path.abspath(elf_file)
        open(elf_path, 'rb').close()  # exist and can be opened by this user
    except IOError as err:
        LOGGER.error('%s', err)
        return 1
    else:
        return OpenOCD.call_cmd(config_file, FLASH_CMD.format(elf_path), verb)


class OpenOCD(object):
    """ Debugger class, implemented as a global variable storage """
    # I don't want to refactor to a simple class for the moment as it should
    # require cleaning a lot of other code, so we use classmethods
    proc = {}
    started = {}

    @classmethod
    def debug_start(cls, config_file, verb=False):
        """ Start a debugger process """
        # kill previous process
        LOGGER.info('Debug start')
        cls.debug_stop(config_file)

        args = cls._ocd_args(config_file, DEBUG_CMD)
        with open(os.devnull, 'w') as fnull:
            # on non verbose, put output to devnull
            out = None if verb else fnull
            cls.proc[config_file] = subprocess.Popen(
                args, stdout=out, stderr=out)

        # Add atexit for debug_stop in case we close it abruptly
        # should be moved in '__init__' when there will be one
        if config_file not in cls.started:
            cls.started[config_file] = True
            atexit.register(cls.debug_stop, config_file)
        LOGGER.info('Debug started')
        return 0

    @classmethod
    def debug_stop(cls, config_file):
        """ Stop the debugger process """
        try:
            LOGGER.info('Debug stop')
            if config_file in cls.proc:
                cls.proc[config_file].terminate()
        except OSError as err:
            LOGGER.error('Debug stop error: %r', err)
        finally:
            cls.proc.pop(config_file, None)
            LOGGER.info('Debug stopped')
        return 0

    @classmethod
    def call_cmd(cls, config_file, command_str, verb=False):
        """ Run the given command_str with init on openocd for config_file.
        If openocd is in 'debug' mode, return an error """
        if config_file in cls.proc:
            LOGGER.error("OpenOCD is in 'debug' mode, stop it to flash/reset")
            return 1

        # Get configuration file
        args_list = cls._ocd_args(config_file, command_str)

        with open(os.devnull, 'w') as fnull:
            # on non verbose, put output to devnull
            cmd_out = None if verb else fnull
            return subprocess.call(args_list, stdout=cmd_out, stderr=cmd_out)

    @staticmethod
    def _ocd_args(config_file, command_str):
        """ Get openocd arguments for given config_file and command_str """
        # get config file
        cfg_file = os.path.abspath(config_file)
        open(cfg_file, 'rb').close()  # exist and can be opened by this user

        # Generate full command arguments
        args = shlex.split(OPENOCD_BASE_CMD.format(cfg_file) + command_str)
        return args
