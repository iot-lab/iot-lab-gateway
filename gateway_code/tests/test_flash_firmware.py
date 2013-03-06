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



class PopenMock(object):
    """
    Dummy Popen implementation for testing
    """
    out = None
    err = None
    returncode = None

    def __init__(self, cmds, stdout, stderr):
        self.returncode = None
        print cmds
        print stdout
        print stderr

    def communicate(self):
        self.returncode = type(self).returncode
        out = type(self).out
        err = type(self).err
        return out, err

    @classmethod
    def setup(cls, out=None, err=None, returncode=None):
        cls.out = out
        cls.err = err
        cls.returncode = returncode




def test_flash():
    import subprocess
    flash = flash_firmware.FlashFirmware('m3')

    out = "STDOUT messages"
    err = "STDERR messages"
    returncode = 0

    PopenMock.setup(out=out, err=err, returncode=returncode)
    with mock.patch('subprocess.Popen', new=PopenMock):
        ret = flash.flash('auauei')

    assert flash.out == out
    assert flash.err == err
    assert ret == returncode




