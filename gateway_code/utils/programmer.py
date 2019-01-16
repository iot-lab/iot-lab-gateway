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


def _node_class(control_node=False):
    board_cfg = board_config.BoardConfig()
    if control_node:
        return board_cfg.cn_class
    elif board_cfg.linux_on_class is not None:
        # Linux open node
        return board_cfg.linux_on_class
    return board_cfg.board_class


def _setup_parser(action):
    parser = argparse.ArgumentParser()
    parser.add_argument('-cn', '--controle-node', action="store_true",
                        help='%s control node' % action)
    if action == 'flash':
        parser.add_argument('firmware', dest='firmware_path', type=str,
                            help="Firmware path")
    return parser


CMD_ERROR = '{} command is not available on {} node'


@log_to_stderr
def flash():
    """ flash node function """
    parser = _setup_parser(flash.__name__)
    opts = parser.parse_args()
    node = _node_class(opts.cn)
    if getattr(node, flash.__name__):
        ret = node.flash(opts.firmware_path)
        if ret == 0:
            print '%s OK\n' % flash.__name__
        else:
            print '%s KO: %d\n' % (flash.__name__, ret)
    else:
        raise ValueError(CMD_ERROR.format(flash.__name__, node.TYPE))


@log_to_stderr
def reset():
    """ reset node function """
    parser = _setup_parser(reset.__name__)
    opts = parser.parse_args()
    node = _node_class(opts.cn)
    if getattr(node, reset.__name__):
        ret = node.reset()
        if ret == 0:
            print '%s OK\n' % reset.__name__
        else:
            print '%s KO: %d\n' % (reset.__name__, ret)
    else:
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
    node = _node_class(opts.cn)
    if (getattr(node, '{}_start'.format(debug.__name__)) and
            getattr(node, '{}_stop'.format(debug.__name__))):
        ret = _debug(node)
        if ret == 0:
            print '%s OK\n' % debug.__name__
        else:
            print '%s KO: %d\n' % (debug.__name__, ret)
    else:
        raise ValueError(CMD_ERROR.format(debug.__name__, node.TYPE))
