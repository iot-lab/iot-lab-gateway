#! /usr/bin/env python
# -*- coding:utf-8 -*-
""" CLI client for openocd_cmd

Usage:
        openocdcmd flash <node> <firmware_path>
        openocdcmd reset <node>

"""
import argparse
from .. import openocd

PARSER = argparse.ArgumentParser()
_SUB = PARSER.add_subparsers()

_FLASH = _SUB.add_parser('flash')
_FLASH.set_defaults(cmd='flash')
_FLASH.add_argument('node', type=str, choices=('CN', 'M3', 'FOX'),)
_FLASH.add_argument('firmware', type=str, help="Firmware name")

_RESET = _SUB.add_parser('reset')
_RESET.set_defaults(cmd='reset')
_RESET.add_argument('node', type=str, choices=('CN', 'M3', 'FOX'))


def _node_config(node):
    """ Get node openocd config for 'node' in ('CN', 'M3', 'FOX') """
    # This is a HACK for the moment, nodes should be deduced otherwise
    from gateway_code.open_node import NodeM3
    from gateway_code.open_node import NodeFox
    from gateway_code.control_node.cn import ControlNode
    _config_files = {
        'CN': ControlNode.OPENOCD_CFG_FILE,
        'M3': NodeM3.OPENOCD_CFG_FILE,
        'FOX': NodeFox.OPENOCD_CFG_FILE,
    }
    return _config_files[node]


def main():
    """ openocd main function """
    opts = PARSER.parse_args()
    cfg_file = _node_config(opts.node)
    ocd = openocd.OpenOCD(cfg_file, verb=True)

    if opts.cmd == 'reset':
        ret = ocd.reset()
    elif opts.cmd == 'flash':
        ret = ocd.flash(opts.firmware)
    else:  # pragma: no cover
        raise ValueError('Uknown Command %s', opts.command)

    if ret == 0:
        print '%s OK\n' % opts.cmd
    else:
        print '%s KO: %d\n' % (opts.cmd, ret)

    return ret
