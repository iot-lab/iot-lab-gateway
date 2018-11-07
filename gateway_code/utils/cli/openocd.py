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

""" CLI client for openocd_cmd

Usage:
        openocd_cmd flash <node> <firmware_path>
        openocd_cmd reset <node>

"""
import signal
import argparse

from gateway_code.nodes import open_node_class, all_open_nodes_types
from gateway_code.control_nodes.cn_iotlab import ControlNodeIotlab
from gateway_code.open_nodes.common.node_openocd import NodeOpenOCDBase
from gateway_code.open_nodes.common.node_edbg import NodeEdbgBase

from gateway_code.utils import openocd
from gateway_code.utils.cli import log_to_stderr


def _node_keys():
    res = ['CN']
    for node_type in sorted(all_open_nodes_types()):
        if (issubclass(open_node_class(node_type), NodeOpenOCDBase) or
                issubclass(open_node_class(node_type), NodeEdbgBase)):
            res.append(node_type.upper())
    return res


def _node_class(node_type):
    if node_type == 'cn':
        return ControlNodeIotlab
    return open_node_class(node_type)


def _setup_parser():
    parser = argparse.ArgumentParser()
    sub_parser = parser.add_subparsers()

    nodes = _node_keys()

    flash = sub_parser.add_parser('flash')
    flash.set_defaults(cmd='flash')
    flash.add_argument('node', type=str, choices=nodes)
    flash.add_argument('firmware', type=str, help="Firmware name")

    reset = sub_parser.add_parser('reset')
    reset.set_defaults(cmd='reset')
    reset.add_argument('node', type=str, choices=nodes)

    debug = sub_parser.add_parser('debug')
    debug.set_defaults(cmd='debug')
    debug.add_argument('node', type=str, choices=nodes)
    return parser


def _debug(ocd):
    """Start debugging, wait for Ctrl+C, and quit."""
    ret = ocd.debug_start()
    if ret:
        return ret
    try:
        print 'Type Ctrl+C to quit'
        signal.pause()
    except KeyboardInterrupt:
        print 'Ctrl+C'
    finally:
        ocd.debug_stop()
    return 0


@log_to_stderr
def main():
    """ openocd main function """
    parser = _setup_parser()
    opts = parser.parse_args()
    node = _node_class(opts.node.lower())
    ocd = openocd.OpenOCD.from_node(node, verb=True)

    if opts.cmd == 'reset':
        ret = ocd.reset()
    elif opts.cmd == 'flash':
        ret = ocd.flash(opts.firmware)
    elif opts.cmd == 'debug':
        ret = _debug(ocd)
    else:  # pragma: no cover
        raise ValueError('Uknown Command {}'.format(opts.cmd))

    if ret == 0:
        print '%s OK\n' % opts.cmd
    else:
        print '%s KO: %d\n' % (opts.cmd, ret)

    return ret
