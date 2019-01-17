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

""" Programmer to flash/reset/debug nodes  """

import signal
import argparse

import gateway_code.board_config as board_config
from gateway_code.utils.cli import log_to_stderr


def _get_node(control_node=False):
    board_cfg = board_config.BoardConfig()
    if control_node:
        return board_cfg.cn_class(board_cfg.node_id, None)
    elif board_cfg.linux_on_class is not None:
        # Linux open node
        return board_cfg.linux_on_class()
    return board_cfg.board_class()


def _setup_parser(action):
    parser = argparse.ArgumentParser()
    parser.add_argument('-cn', '--controle-node', dest="cn",
                        action="store_true", help='%s control node' % action)
    if action == 'flash':
        parser.add_argument('firmware', help="Firmware path")
    return parser


def _print_result(ret, cmd):
    if ret == 0:
        print '%s OK\n' % cmd
    else:
        print '%s KO: %d\n' % (cmd, ret)


CMD_ERROR = '{} command is not available on {} node'


@log_to_stderr
def flash():
    """ flash node function """
    parser = _setup_parser(flash.__name__)
    opts = parser.parse_args()
    node = _get_node(opts.cn)
    if hasattr(node, flash.__name__):
        ret = node.flash(opts.firmware)
        _print_result(ret, flash.__name__)
        return ret
    raise ValueError(CMD_ERROR.format(flash.__name__, node.TYPE))


@log_to_stderr
def reset():
    """ reset node function """
    parser = _setup_parser(reset.__name__)
    opts = parser.parse_args()
    node = _get_node(opts.cn)
    if hasattr(node, reset.__name__):
        ret = node.reset()
        _print_result(ret, reset.__name__)
        return ret
    raise ValueError(CMD_ERROR.format(reset.__name__, node.TYPE))


def _debug(node):
    """Start debugging, wait for Ctrl+C, and quit."""
    ret = node.debug_start()
    if ret:
        return ret
    try:
        print 'Type Ctrl+C to quit'
        signal.pause()
    except KeyboardInterrupt:
        print 'Ctrl+C'
    finally:
        node.debug_stop()
    return 0


@log_to_stderr
def debug():
    """ debug node function """
    parser = _setup_parser(debug.__name__)
    opts = parser.parse_args()
    node = _get_node(opts.cn)
    if (hasattr(node, '{}_start'.format(debug.__name__)) and
            hasattr(node, '{}_stop'.format(debug.__name__))):
        ret = _debug(node)
        _print_result(ret, debug.__name__)
        return ret
    raise ValueError(CMD_ERROR.format(debug.__name__, node.TYPE))
