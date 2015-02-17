#! /usr/bin/env python
# -*- coding:utf-8 -*-


"""
OpenOCD commands
"""

import shlex
import subprocess

import os
import gateway_code.config as config

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


def reset(node, verb=False):
    """ Reset """
    return _run_openocd_command(node, RESET_CMD, verb)


def flash(node, elf_file, verb=False):
    """ Flash firmware """
    try:
        # get the absolute file path required for openocd
        elf_path = os.path.abspath(elf_file)
        open(elf_path, 'rb').close()  # exist and can be opened by this user
    except IOError as err:
        LOGGER.error('%s', err)
        return 1, ""

    return _run_openocd_command(node, FLASH_CMD.format(elf_path), verb)


class Debug(object):
    """ Debugger class, implemented as a global variable storage """
    # I don't want to refactor to a simple class for the moment as it should
    # require cleaning a lot of other code
    proc = {}

    @classmethod
    def start(cls, node, verb=False):
        """ Start a debugger process """
        # kill previous process
        LOGGER.debug('Debug_start')
        cls.stop(node)

        args = _openocd_args(node, DEBUG_CMD)
        with open(os.devnull, 'w') as fnull:
            # on non verbose, put output to devnull
            out = None if verb else fnull
            cls.proc[node] = subprocess.Popen(args, stdout=out, stderr=out)
        return 0

    @classmethod
    def stop(cls, node):
        """ Stop the debugger process """
        try:
            LOGGER.debug('Debug_stop process')
            if cls.proc.setdefault(node, None) is not None:
                cls.proc[node].terminate()
        except OSError as err:
            LOGGER.debug('Debug_stop process error: %r', err)
        finally:
            del cls.proc[node]
        return 0


def _run_openocd_command(node, command_str, verb=False):
    """ Run the given command with init and teardown on openocd for 'node' """

    # Get configuration file
    args_list = _openocd_args(node, command_str)

    with open(os.devnull, 'w') as fnull:
        # on non verbose, put output to devnull
        cmd_out = None if verb else fnull
        ret = subprocess.call(args_list, stdout=cmd_out, stderr=cmd_out)

    return ret


def _openocd_args(node, command_str):
    """ Get openocd arguments for given node and command_str """
    # get config file
    assert node in config.NODES_CFG.keys()
    _file = os.path.join(config.STATIC_FILES_PATH,
                         config.NODES_CFG[node]['openocd_cfg_file'])
    cfg_file = os.path.abspath(_file)
    open(cfg_file, 'rb').close()  # exist and can be opened by this user

    # Generate full command arguments
    args = shlex.split(OPENOCD_BASE_CMD.format(cfg_file) + command_str)
    return args


#
# Command line functions
#

def _parse_arguments(args):
    """
    Parse arguments:
        flash node firmware_path
        reset node

    :param args: arguments, without the script name == sys.argv[1:]
    :type args: list

    """
    import argparse

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()

    flash_p = sub.add_parser('flash')
    flash_p.set_defaults(cmd='flash')
    flash_p.add_argument('node', type=str, choices=config.NODES)
    flash_p.add_argument('firmware', type=str, help="Firmware name")

    flash_p = sub.add_parser('reset')
    flash_p.set_defaults(cmd='reset')
    flash_p.add_argument('node', type=str, choices=config.NODES)

    arguments = parser.parse_args(args)
    return arguments


def _main(argv):
    """
    Command line main function
    """

    import sys
    namespace = _parse_arguments(argv[1:])

    if namespace.cmd == 'reset':
        ret = reset(namespace.node, verb=True)
    elif namespace.cmd == 'flash':
        ret = flash(namespace.node, namespace.firmware, verb=True)
    else:  # pragma: no cover
        raise ValueError('Uknown Command %s', namespace.command)

    if ret == 0:
        sys.stderr.write('%s OK\n' % namespace.cmd)
    else:
        sys.stderr.write('%s KO: %d\n' % (namespace.cmd, ret))

    return ret
