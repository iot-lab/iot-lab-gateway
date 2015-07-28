#! /usr/bin/env python
# -*- coding:utf-8 -*-

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
