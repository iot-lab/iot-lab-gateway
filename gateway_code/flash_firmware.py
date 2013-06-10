#! /usr/bin/env python
# -*- coding:utf-8 -*-


"""
flash_firmware script
"""

import subprocess, shlex
import os
from gateway_code import config


import logging
LOGGER = logging.getLogger('gateway_code')

FLASH_CMD = """
          openocd --debug=0
              -f "%s"
              -f "target/stm32f1x.cfg"
              -c "init"
              -c "targets"
              -c "reset halt"
              -c "reset init"
              -c "flash write_image erase %s"
              -c "verify_image %s"
              -c "reset run"
              -c "shutdown"
"""

def flash(node, elf_file):
    """
    Flash firmware
    """

    # configure Node
    if node not in config.NODES_CFG:
        raise ValueError, 'Unknown node, not in %r' \
                % config.NODES_CFG.keys()
    cfg_file = os.path.abspath(config.STATIC_FILES_PATH + '/' + \
            config.NODES_CFG[node]['openocd_cfg_file'])

    # get the absolute file path required for openocd
    absolute_file_path = os.path.abspath(elf_file)

    if not os.path.isfile(cfg_file):
        import errno
        raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), cfg_file)

    if not os.path.isfile(absolute_file_path):
        LOGGER.error('Firmware not found: %s', absolute_file_path)
        return 1, "", ""

    # flash_cmd
    cmd = FLASH_CMD % (cfg_file, absolute_file_path, absolute_file_path)
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
        [node, firmware_path]

    :param args: arguments, without the script name == sys.argv[1:]
    :type args: list

    """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('node', type=str, choices=config.NODES,
            help="Node selection")
    parser.add_argument('firmware', type=str, help="Firmware name")
    arguments = parser.parse_args(args)

    return arguments.node, arguments.firmware


def main(args):
    """
    Command line main function
    """
    import sys

    node, firmware = parse_arguments(args[1:])

    ret_val, out, err = flash(node, firmware)
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


