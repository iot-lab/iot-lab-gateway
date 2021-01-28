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

""" Programmer to flash/reset/debug nodes  """

import os
import signal
import argparse

import gateway_code.board_config as board_config
from gateway_code.utils.cli import log_to_stderr
from gateway_code import common


_FLASH = 'flash'
_RESET = 'reset'
_DEBUG = 'debug'


def _setup_parser(cmd, board_cfg):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-q', '--quiet',
        action='store_true', help='Disable verbose output'
    )
    if board_cfg.cn_type == 'iotlab' and not board_cfg.linux_on_class:
        parser.add_argument('-cn', '--control-node', dest="cn",
                            action="store_true",
                            help='%s control node' % cmd)
    if cmd == 'flash':
        parser.add_argument('firmware', nargs='?', help='Firmware path')
        parser.add_argument(
            '--bin',
            action='store_true',
            help='use if firmware is a binary file '
        )
        parser.add_argument(
            '--offset', default=0, type=int,
            help='offset at which to flash the binary file'
        )
    return parser.parse_args()


def _get_node(board_cfg, control_node=False):
    if control_node:
        return board_cfg.cn_class(board_cfg.node_id, None)
    if board_cfg.linux_on_class is not None:
        # Linux open node
        return board_cfg.linux_on_class()
    return board_cfg.board_class()


def _print_result(ret, cmd, node=None):
    if ret == 0:
        print('{} OK\n'.format(cmd))
    elif ret == -1:
        print('error: {} not supported for board {}\n'.format(cmd, node))
    elif ret == -2:
        print('error: {} too few arguments\n'.format(cmd))
    else:
        print('{} KO: {}\n'.format(cmd, ret))


@log_to_stderr
def reset():
    """ reset node function """
    board_cfg = board_config.BoardConfig()
    opts = _setup_parser(_RESET, board_cfg)
    control_node = opts.cn if hasattr(opts, 'cn') else False
    node = _get_node(board_cfg, control_node)
    if node.programmer is not None:
        if not opts.quiet:
            node.programmer.out = None
        ret = node.reset()
    else:
        ret = -1
    _print_result(ret, _RESET, node.TYPE)
    return ret


@log_to_stderr
def flash():
    """ flash node function """
    board_cfg = board_config.BoardConfig()
    firmware = os.getenv('FW')
    opts = _setup_parser(_FLASH, board_cfg)
    control_node = opts.cn if hasattr(opts, 'cn') else False
    node = _get_node(board_cfg, control_node)
    if firmware is not None and not control_node:
        if firmware == 'idle':
            firmware = node.FW_IDLE
        if firmware == 'autotest':
            firmware = node.FW_AUTOTEST
    else:
        firmware = opts.firmware

    if firmware is None:
        ret = -2
        _print_result(ret, _FLASH)
        return ret

    if node.programmer is None:
        ret = -1
    else:
        try:
            firmware_path = common.abspath(firmware)
        except IOError as err:
            print(err)
            return 1
        if not opts.quiet:
            node.programmer.out = None
        ret = node.flash(firmware_path, opts.bin, opts.offset)

    _print_result(ret, _FLASH, node.TYPE)
    return ret


def _debug(node):
    """Start debugging, wait for Ctrl+C, and quit."""
    ret = node.debug_start()
    if ret:
        return ret
    try:
        print('Type Ctrl+C to quit')
        signal.pause()
    except KeyboardInterrupt:
        print('Ctrl+C')
    finally:
        node.debug_stop()
    return 0


@log_to_stderr
def debug():
    """ debug node function """
    board_cfg = board_config.BoardConfig()
    opts = _setup_parser(_DEBUG, board_cfg)
    control_node = opts.cn if hasattr(opts, 'cn') else False
    node = _get_node(board_cfg, control_node)
    start_debug = hasattr(node, '{}_start'.format(_DEBUG))
    stop_debug = hasattr(node, '{}_stop'.format(_DEBUG))
    ret = _debug(node) if (start_debug and stop_debug) else -1
    _print_result(ret, _DEBUG, node.TYPE)
    return ret
