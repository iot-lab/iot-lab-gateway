#! /usr/bin/env python


import sys

import re
import mock
from cStringIO import StringIO

# import package code from source folder if not installed
from os.path import dirname, abspath
current_folder = dirname(abspath(__file__))
source_folder = dirname(dirname(current_folder))
sys.path.append(source_folder)

import common
from gateway_code import flash_firmware


@mock.patch('subprocess.Popen', common.PopenMock)
class TestsFlashMethods:
    """
    Tests flash_firmware methods
    """
    import subprocess
    def test_node_detection(self):
        """
        Test node detection
        """

        for node in ('m3', 'gwt', 'a8'):
            ret, out, err = flash_firmware.flash(node, 'filename')

        try:
            node = 'INEXISTANT_ NODE'
            ret, out, err = flash_firmware.flash(node, 'filename')
        except:
            pass
        else:
            assert 0, 'Non existant node not detected'

    def test_flash_OK(self):
        """
        Test with a flash with a successfull call
        """

        mock_out = "STDOUT messages"
        mock_err = ""
        mock_ret = 0
        filename = 'TEST_FILENAME'
        common.PopenMock.setup(out=mock_out, err=mock_err, returncode=mock_ret)

        ret, out, err = flash_firmware.flash('m3', filename)

        assert mock_out == out
        assert mock_err == err
        assert mock_ret == ret
        assert filename in "".join(common.PopenMock.args)


    def test_flash_Error(self):
        """
        Test with a flash with a unsuccessfull call
        """

        mock_out = "STDOUT on error"
        mock_err = "STDERR on error"
        mock_ret = 42
        filename = 'TEST_FILENAME'
        common.PopenMock.setup(out=mock_out, err=mock_err, returncode=mock_ret)

        ret, out, err = flash_firmware.flash('m3', filename)

        assert mock_out == out
        assert mock_err == err
        assert mock_ret == ret
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
    @mock.patch.object(flash_firmware, 'flash')
    def test_normal_run(self, mock_fct):
        """
        Running command line with m3
        """
        mock_fct.return_value = (0, 'OUT', 'ErrorRunMessage')
        try:
            ret = flash_firmware.main(['flash_firmware.py', 'm3', '/dev/null'])
        except SystemExit, ret:
            assert 0
        else:
            print captured_err.getvalue()
            assert re.search('OUT', captured_err.getvalue())
            assert ret == 0
        assert mock_fct.called


    @mock.patch.object(flash_firmware, 'flash')
    def test_error_run(self, mock_fct):
        """
        Running command line with error during run
        """
        mock_fct.return_value = (42, 'OUT', 'ErrorRunMessage')
        try:
                ret = flash_firmware.main(['flash_firmware.py', 'm3', '/dev/null'])
        except SystemExit, ret:
            assert 0
        else:
            err = captured_err.getvalue()
            print err
            assert re.search('KO! return value', err)
            assert re.search('ErrorRunMessage', err)
            assert ret == 42
        assert mock_fct.called



# I couldn't mock the main function so I use a working 'sys.argv'
@mock.patch('sys.argv', ['cmd_name', '--help'])
def test_program_call():
    """
    Simulate command line call
    """
    captured_out = StringIO()
    import runpy
    try:
        with mock.patch('sys.stdout', captured_out):
            runpy.run_module('gateway_code.flash_firmware', \
                    run_name='__main__', alter_sys=True)
    except SystemExit, ret:
        assert ret.code == 0
        assert re.search('help', captured_out.getvalue())
    else:
        assert 0

