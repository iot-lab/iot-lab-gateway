#! /usr/bin/env python
# -*- coding:utf-8 -*-


"""
FlashFirmware script
"""

import argparse
import sys
from subprocess import Popen, PIPE
import shlex



# import common configuration
import config



class FlashFirmware():
    """
    FlashFirmware class

    Used to flash m3, a8 or gwt M3 nodes
    """

    def __init__(self, cfg_file):
        self.cfg_file = cfg_file
        self.err = None
        self.out = None

    def flash(self, elf_file):
        """
        Flash firmware
        Argument should be the full path to the firmware
        Return 0 if OK
        Return openocd return value on error
        """

        # flash_cmd
        cmd = """
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

        """ % (self.cfg_file, elf_file, elf_file)
        cmd_list = shlex.split(cmd)

        # Run openocd
        openocd = Popen(cmd_list, stdout=PIPE, stderr=PIPE)
        out, err = openocd.communicate() # nothing is written to stdout
        ret = openocd.returncode

        self.out = out
        self.err = err

        # Check execution
        if ret != 0:
            # logging ???
            pass

        return ret



def parse_arguments(args):
    """
    Parsing arguments:

    script.py node firmware.elf
    Only pass arguments to function without script name

    """
    parser = argparse.ArgumentParser()
    parser.add_argument('node', type=str, choices=config.NODES,
            help="Node selection")
    parser.add_argument('firmware', type=str, help="Firmware name")
    arguments = parser.parse_args(args)

    return arguments.node, arguments.firmware



if __name__ == '__main__':


    NODE, FIRMWARE = parse_arguments(sys.argv[1:])
    CONFIG_FILE =  config.CONFIG_FILES_PATH + '/' + config.NODES_CFG[NODE]

    FLASH = FlashFirmware(CONFIG_FILE)
    RET_VAL = FLASH.flash(FIRMWARE)
    if RET_VAL != 0:
        # traiter les sorties
        sys.stderr.write("Out:\n")
        sys.stderr.write(FLASH.out)
        sys.stderr.write("Err:\n")
        sys.stderr.write(FLASH.err)
        sys.stderr.write("\n\n")
        sys.stderr.write("KO! return value: %d\n" % RET_VAL)
    else:
        sys.stderr.write("OK")



