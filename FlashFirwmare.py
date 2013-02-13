#! /usr/bin/env python
"""
FlashFirmware class
"""

import argparse
import sys
import subprocess
import shlex



CONFIG_FILES_PATH = '~/bin'
NODES_CFG   = {
    'gwt':'fiteco-gwt.cfg',
    'm3': 'fiteco-m3.cfg',
    'a8': 'fiteco-a8.cfg'
    }

NODES = NODES_CFG.keys()




class UpdateFirmware():
  def __init__(self, cfg_file):
    self.cfg_file = cfg_file

  def flash(self, elf_file):
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

    """ % (self.cfg_file, self.elf_file, self.elf_file)

    openocd = subprocess.Popen(shlex.split(cmd))
    out, err = openocd.communicate()

    print "Out : %s" % out
    print "Err : %s" % err

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

    updatefirmware = UpdateFirmware(CONFIG_FILE)
    updatefirmware.flash(FIRMWARE)


