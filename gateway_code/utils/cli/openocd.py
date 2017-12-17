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
        openocdcmd flash <node> <firmware_path>
        openocdcmd reset <node>

"""
import signal
import argparse
from .. import openocd
from . import log_to_stderr

PARSER = argparse.ArgumentParser()
_SUB = PARSER.add_subparsers()

_FLASH = _SUB.add_parser('flash')
_FLASH.set_defaults(cmd='flash')
_FLASH.add_argument('node', type=str, choices=('CN', 'M3', 'FOX', 'SAMR21'),)
_FLASH.add_argument('firmware', type=str, help="Firmware name")

_RESET = _SUB.add_parser('reset')
_RESET.set_defaults(cmd='reset')
_RESET.add_argument('node', type=str, choices=('CN', 'M3', 'FOX', 'SAMR21'))

_DEBUG = _SUB.add_parser('debug')
_DEBUG.set_defaults(cmd='debug')
_DEBUG.add_argument('node', type=str, choices=('CN', 'M3', 'FOX'))


def _node_class(node):
    """ Get node openocd config for 'node' in ('CN', 'M3', 'FOX', 'SAMR21') """
    # This is a HACK for the moment, nodes should be deduced otherwise
    from gateway_code.open_nodes.node_m3 import NodeM3
    from gateway_code.open_nodes.node_fox import NodeFox
    from gateway_code.open_nodes.node_samr21 import NodeSamr21
    from gateway_code.control_nodes.cn_iotlab import ControlNodeIotlab
    _config_files = {
        'CN': ControlNodeIotlab,
        'M3': NodeM3,
        'FOX': NodeFox,
        'SAMR21': NodeSamr21,
    }
    return _config_files[node]


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
    opts = PARSER.parse_args()
    node = _node_class(opts.node)
    ocd = openocd.OpenOCD.from_node(node, verb=True)

    if opts.cmd == 'reset':
        ret = ocd.reset()
    elif opts.cmd == 'flash':
        ret = ocd.flash(opts.firmware)
    elif opts.cmd == 'debug':
        ret = _debug(ocd)
    else:  # pragma: no cover
        raise ValueError('Uknown Command {}'.format(opts.command))

    if ret == 0:
        print '%s OK\n' % opts.cmd
    else:
        print '%s KO: %d\n' % (opts.cmd, ret)

    return ret
