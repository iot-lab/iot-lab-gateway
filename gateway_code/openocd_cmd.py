#! /usr/bin/env python
# -*- coding:utf-8 -*-


"""
OpenOCD commands
"""

import shlex
import subprocess
from subprocess import PIPE

from os.path import abspath
from gateway_code import config

import logging
LOGGER = logging.getLogger('gateway_code')

OPENOCD_BASE_CMD = '''
    openocd --debug=0
        -f "%s"
        -f "target/stm32f1x.cfg"
        -c "init"
        -c "targets"
        %s
        -c "reset run"
        -c "shutdown"
        '''

RESET_CMD = ''
FLASH_CMD = '''
        -c "reset halt"
        -c "reset init"
        -c "flash write_image erase %s"
        -c "verify_image %s"
'''


def reset(node):
    """
    Reset
    """
    reset_cmd = RESET_CMD
    return _run_openocd_command(node, reset_cmd)


def flash(node, elf_file):
    """
    Flash firmware
    """
    try:
        # get the absolute file path required for openocd
        elf_path = abspath(elf_file)
        open(elf_path, 'rb').close()  # exist and can be opened by this user
    except IOError as err:
        LOGGER.error('%s', err)
        return 1, ""

    flash_cmd = FLASH_CMD % (elf_path, elf_path)
    return _run_openocd_command(node, flash_cmd)


def _run_openocd_command(node, command_str):
    """
    Run the given command with init and teardown on openocd for 'node'
    """

    # Get configuration file
    try:
        cfg_file = abspath(
            '%s/%s' % (config.STATIC_FILES_PATH,
                       config.NODES_CFG[node]['openocd_cfg_file']))
        open(cfg_file, 'rb').close()  # exist and can be opened by this user
    except KeyError:
        raise ValueError('Unknown node, not in %r', config.NODES_CFG.keys())

    args_list = shlex.split(OPENOCD_BASE_CMD % (cfg_file, command_str))
    # Run openocd
    openocd = subprocess.Popen(args_list, stderr=PIPE)
    outputs = openocd.communicate()
    ret = openocd.returncode
    return ret, outputs


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
        ret, outputs = reset(namespace.node)
    elif namespace.cmd == 'flash':
        ret, outputs = flash(namespace.node, namespace.firmware)
    else:  # pragma: no cover
        raise ValueError('Uknown Command %s', namespace.command)

    if ret == 0:
        sys.stderr.write('%s OK\n' % namespace.cmd)
    else:
        sys.stderr.write('%s KO: %d\n' % (namespace.cmd, ret))
        sys.stderr.write(outputs[1])

    return ret
