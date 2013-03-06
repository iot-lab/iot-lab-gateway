#! /usr/bin/env python

import sys
sys.path.append("../../")

import re
import mock
from cStringIO import StringIO

import common

from gateway_code import flash_firmware


def test_init():
    flash = flash_firmware.FlashFirmware('m3')
    assert flash.node == 'm3'
    assert re.search('fiteco-m3.cfg', flash.cfg_file)
    assert flash.out == None
    assert flash.err == None

    return 0


def test_flash_OK():
    import subprocess
    flash = flash_firmware.FlashFirmware('m3')

    out = "STDOUT messages"
    err = ""
    returncode = 0
    filename = 'TEST_FILENAME'

    common.PopenMock.setup(out=out, err=err, returncode=returncode)
    with mock.patch('subprocess.Popen', new=common.PopenMock):
        ret = flash.flash('TEST_FILENAME')

    assert flash.out == out
    assert flash.err == err
    assert ret == returncode
    assert filename in "".join(common.PopenMock.args)


def test_flash_Error():
    import subprocess
    flash = flash_firmware.FlashFirmware('m3')

    out = "STDOUT on error"
    err = "STDERR on error"
    returncode = 42

    common.PopenMock.setup(out=out, err=err, returncode=returncode)
    with mock.patch('subprocess.Popen', new=common.PopenMock):
        ret = flash.flash('auauei')

    assert flash.out == out
    assert flash.err == err
    assert ret == returncode





