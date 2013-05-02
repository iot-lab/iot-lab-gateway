#! /usr/bin/env python
# -*- coding:utf-8 -*-


"""
reset script
"""

import sys
import subprocess

import shlex

import os


# import common configuration
from gateway_code import config


RESET_CMD = """
        openocd
            --debug=0
            -f "%s"
            -f "target/stm32f1x.cfg"
            -c "init"
            -c "targets"
            -c "reset run"
            -c "shutdown"
"""

def reset(node):
    """
    Reset
    """

    # configure Node
    if node not in config.NODES_CFG:
        raise ValueError, 'Unknown node, not in %r' \
                % config.NODES_CFG.keys()
    cfg_file = os.path.abspath(config.STATIC_FILES_PATH + '/' + \
            config.NODES_CFG[node]['openocd_cfg_file'])

    if not os.path.isfile(cfg_file):
        import errno
        raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), cfg_file)

    # flash_cmd
    cmd = RESET_CMD % (cfg_file)
    cmd_list = shlex.split(cmd)

    # Run openocd
    openocd = subprocess.Popen(cmd_list, \
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = openocd.communicate() # nothing is written to stdout
    ret = openocd.returncode

    return ret, out, err



def parse_arguments(args):
    """
    Parse arguments:
        [node]

    :param args: arguments, without the script name == sys.argv[1:]
    :type args: list

    """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('node', type=str, choices=config.NODES,
            help="Node selection")
    arguments = parser.parse_args(args)

    return arguments.node


def main(args):
    """
    Command line main function
    """

    node = parse_arguments(args[1:])

    ret_val, out, err = reset(node)
    if ret_val != 0:
        # traiter les sorties
        sys.stderr.write("Out:\n")
        sys.stderr.write(out)
        sys.stderr.write("Err:\n")
        sys.stderr.write(err)
        sys.stderr.write("\n\n")
        sys.stderr.write("KO! return value: %d\n" % ret_val)
    else:
        sys.stderr.write("OK\n")

    return ret_val


