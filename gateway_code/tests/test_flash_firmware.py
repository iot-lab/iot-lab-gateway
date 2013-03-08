#! /usr/bin/env python

import sys
sys.path.append("../../")

import re
import mock
from cStringIO import StringIO

import common

from gateway_code import flash_firmware


@mock.patch('subprocess.Popen', common.PopenMock)
class TestsFlashMethods:
    """
    Tests flash_firmware methods
    """
    import subprocess
    def test_init(self):
        """
        Test object creation
        """

        NODE='m3'
        flash = flash_firmware.FlashFirmware(NODE)

        assert flash.node == NODE
        assert re.search('fiteco-m3.cfg', flash.cfg_file)
        assert flash.out == None
        assert flash.err == None


        NODE='gwt'
        flash = flash_firmware.FlashFirmware(NODE)
        assert flash.node == NODE

        NODE='a8'
        flash = flash_firmware.FlashFirmware(NODE)
        assert flash.node == NODE

        try:
            NODE='INEXISTANT NODE'
            flash = flash_firmware.FlashFirmware(NODE)
        except:
            pass
        else:
            assert 0, 'Non existant node not detected'

    def test_flash_OK(self):
        """
        Test with a flash with a successfull call
        """

        out = "STDOUT messages"
        err = ""
        returncode = 0
        filename = 'TEST_FILENAME'
        common.PopenMock.setup(out=out, err=err, returncode=returncode)

        flash = flash_firmware.FlashFirmware('m3')
        ret = flash.flash('TEST_FILENAME')

        assert flash.out == out
        assert flash.err == err
        assert ret == returncode
        assert filename in "".join(common.PopenMock.args)


    def test_flash_Error(self):
        """
        Test with a flash with a unsuccessfull call
        """

        out = "STDOUT on error"
        err = "STDERR on error"
        returncode = 42
        filename = 'TEST_FILENAME'
        common.PopenMock.setup(out=out, err=err, returncode=returncode)

        flash = flash_firmware.FlashFirmware('m3')
        ret = flash.flash(filename)

        assert flash.out == out
        assert flash.err == err
        assert ret == returncode
        assert filename in "".join(common.PopenMock.args)




# Command line tests

from cStringIO import StringIO
captured_out = StringIO()
captured_err = StringIO()
@mock.patch('sys.stdout', captured_out)
@mock.patch('sys.stderr', captured_err)
class TestsCommandLineCalls:
    def test_error_no_arguments(self):
        """
        Running command line without arguments
        """
        try:
            ret = flash_firmware.main(['flash_firmware.py'])
        except SystemExit, ret:
            assert ret.code != 0
        else:
            assert 0


    def test_error_help(self):
        """
        Running command line with --help
        """
        try:
            ret = flash_firmware.main(['flash_firmware.py', '-h'])
        except SystemExit, ret:
            assert ret.code == 0
            assert re.search('help', captured_out.getvalue())
        else:
            assert 0




    # look to replace mock.patch with simple 'mock' class (might be better here I think
    @mock.patch.object(flash_firmware.FlashFirmware, 'flash', lambda s,x: 0)
    def test_normal_run(self):
        """
        Running command line with m3
        """
        try:
            ret = flash_firmware.main(['flash_firmware.py', 'm3', '/dev/null'])
        except SystemExit, ret:
            assert 0
        else:
            print captured_err.getvalue()
            assert re.search('OK', captured_err.getvalue())
            assert ret == 0


    def test_error_run(self):
        """
        Running command line with error during run
        """
        try:
            with mock.patch('gateway_code.flash_firmware.FlashFirmware') as mock_class:
                instance = mock_class.return_value
                instance.out = 'OUT'
                instance.err = 'ErrorRunMessage'
                instance.flash.return_value = 42
                ret = flash_firmware.main(['flash_firmware.py', 'm3', '/dev/null'])
        except SystemExit, ret:
            assert 0
        else:
            err = captured_err.getvalue()
            assert re.search('KO! return value', err)
            assert re.search('ErrorRunMessage', err)
            assert ret == 42

