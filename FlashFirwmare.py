#! /usr/bin/env python
# -*- coding:utf-8 -*-


"""
FlashFirmware script
"""

import argparse
import sys
from subprocess import Popen, PIPE
import shlex



CONFIG_FILES_PATH = '/home/root/bin'
NODES_CFG   = {
    'gwt':'fiteco-gwt.cfg',
    'm3': 'fiteco-m3.cfg',
    'a8': 'fiteco-a8.cfg'
    }

NODES = NODES_CFG.keys()


class FlashFirmware():
    """
    FlashFirmware class

    Used to flash m3, a8 or gwt M3 nodes
    """

    def __init__(self, cfg_file):
        self.cfg_file = cfg_file

    def flash(self, elf_file):
        """
        Flash firmware
        Argument should be the full path to the firmware
        Return 0 if OK
        Return openocd return value on error
        """

        # flash_cmd
        cmd = """
          openocd -f "%s"
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
        out, err = openocd.communicate()
        ret = openocd.returncode


        # Check execution
        if ret == 0:
            print 'Ça marche OK'
        else:
            sys.stderr.write("Ca a merdé: %d\n" % ret)
            sys.stderr.write("Write stderr to Log\n")
            # write stderr to log
            # print err >> log_num_date_
            return ret

        return 0



def parse_arguments(args):
    """
    Parsing arguments:

    script.py node firmware.elf
    Only pass arguments to function without script name

    """
    parser = argparse.ArgumentParser()
    parser.add_argument('node', type=str, choices=NODES,
            help="Node selection")
    parser.add_argument('firmware', type=str, help="Firmware name")
    arguments = parser.parse_args(args)

    return arguments.node, arguments.firmware




if __name__ == '__main__':
    NODE, FIRMWARE = parse_arguments(sys.argv[1:])

    print "node %s" % NODE
    print "firmware %s" % FIRMWARE
    CONFIG_FILE =  CONFIG_FILES_PATH + '/' + NODES_CFG[NODE]

    print 'config_file %s' % CONFIG_FILE

    FLASH = FlashFirmware(CONFIG_FILE)
    FLASH.flash(FIRMWARE)


