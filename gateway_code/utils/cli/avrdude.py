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


""" CLI client for avrdude_cmd

Usage:
        avrdudecmd flash <node> <firmware_path>

"""
import argparse
from .. import avrdude

PARSER = argparse.ArgumentParser()
_SUB = PARSER.add_subparsers()

_FLASH = _SUB.add_parser('flash')
_FLASH.set_defaults(cmd='flash')
_FLASH.add_argument('node', type=str, choices=('LEONARDO', 'MEGA'),)
_FLASH.add_argument('firmware', type=str, help="Firmware name")


def _node_type(node):
    """ Get node avrdude config for 'node' in ('LEONARDO') """
    from gateway_code.open_nodes.node_leonardo import NodeLeonardo
    _config = {
        'LEONARDO': NodeLeonardo,
    }
    return _config[node]


def main():
    """ openocd main function """
    opts = PARSER.parse_args()
    node = _node_type(opts.node)
    ret = avrdude.AvrDude.trigger_bootloader(node.TTY, node.TTY_PROG)
    avr = avrdude.AvrDude(node.AVRDUDE_CONF, verb=True)

    if opts.cmd == 'flash':
        ret += avr.flash(opts.firmware)
    else:  # pragma: no cover
        raise ValueError('Uknown Command %s', opts.command)

    if ret == 0:
        print '%s OK\n' % opts.cmd
    else:
        print '%s KO: %d\n' % (opts.cmd, ret)

    return ret
