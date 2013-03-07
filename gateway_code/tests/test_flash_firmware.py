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
    with mock.patch('subprocess.Popen', common.PopenMock):
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
    with mock.patch('subprocess.Popen', common.PopenMock):
        ret = flash.flash('auauei')

    assert flash.out == out
    assert flash.err == err
    assert ret == returncode




# Command line tests

def test_error_no_arguments():
    """
    Running command line without arguments
    """
    from cStringIO import StringIO
    try:
        sys.stdout = captured_out = StringIO()
        sys.stderr = captured_err = StringIO()
        with mock.patch('sys.stdout', captured_out):
            with mock.patch('sys.stderr', captured_err):
                ret = flash_firmware.main(['flash_firmware.py'])
    except SystemExit, ret:
        assert ret.code != 0
    else:
        assert 0


def test_error_help():
    """
    Running command line with --help
    """
    from cStringIO import StringIO
    try:
        captured_out = StringIO()
        captured_err = StringIO()
        with mock.patch('sys.stdout', captured_out):
            with mock.patch('sys.stderr', captured_err):
                ret = flash_firmware.main(['flash_firmware.py', '-h'])
    except SystemExit, ret:
        assert ret.code == 0
    else:
        assert 0


@mock.patch.object(flash_firmware.FlashFirmware, 'flash', lambda s,x: 0)
def test_normal_run():
    """
    Running command line with m3
    """
    from cStringIO import StringIO
    try:
        captured_out = StringIO()
        captured_err = StringIO()
        with mock.patch('sys.stdout', captured_out):
            with mock.patch('sys.stderr', captured_err):
                print 'Lala'
                ret = flash_firmware.main(['flash_firmware.py', 'm3', '/dev/null'])
    except SystemExit, ret:
        assert 0
    else:
        print captured_err.getvalue()
        assert re.search('OK', captured_err.getvalue())
        assert ret == 0


# @mock.patch.object(flash_firmware.FlashFirmware, 'flash', lambda s,x: 1)
# def test_error_run():
#     """
#     Running command line with m3
#     """
#     from cStringIO import StringIO
#     try:
#         captured_out = StringIO()
#         captured_err = StringIO()
#         with mock.patch('sys.stdout', captured_out):
#             with mock.patch('sys.stderr', captured_err):
#                 print 'Lala'
#                 ret = flash_firmware.main(['flash_firmware.py', 'm3', '/dev/null'])
#     except SystemExit, ret:
#         assert 0
#     else:
#         print captured_err.getvalue()
#         assert re.search('OK', captured_err.getvalue())
#         assert ret == 0


