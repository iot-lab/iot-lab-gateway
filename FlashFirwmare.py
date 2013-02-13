#! /usr/bin/env python

import subprocess
import shlex

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





if __name__ == '__main__':
    pass


