#! /usr/bin/env python

import sys
sys.path.append("../../")

import re
import mock

from gateway_code import flash_firmware


def test_init():
    flash = flash_firmware.FlashFirmware('m3')
    assert flash.node == 'm3'
    assert re.search('fiteco-m3.cfg', flash.cfg_file)
    assert flash.out == None
    assert flash.err == None

    return 0



class PopenMock():
    def __init__(self, cmds, stdout, stderr):
        print cmds
        print stdout
        print stderr

    def communicate():
        self.returncode = 0
        assert False, 'Test assert'
        return "STDOUT messages", "STDERR messages"



@mock.patch('subprocess.Popen', PopenMock)
def test_flash():
    import subprocess
    subprocess.Popen = PopenMock
    flash = flash_firmware.FlashFirmware('m3')
    ret = flash.flash('auauei')
    return ret




