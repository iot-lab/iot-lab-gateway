#! /usr/bin/env python


import sys

import re
import mock
from cStringIO import StringIO

import os
from os.path import dirname, abspath

from gateway_code import reset


CURRENT_DIR = dirname(abspath(__file__)) + '/'
STATIC_DIR  = CURRENT_DIR + 'static/' # using the 'static' symbolic link

from subprocess import PIPE
@mock.patch('gateway_code.reset.config.STATIC_FILES_PATH', new=STATIC_DIR)
@mock.patch('subprocess.Popen')
class TestsResetMethods:
    """
    Tests reset functions
    """
    def test_node_detection(self, mock_popen):
        """
        Test node detection
        """
        # config mock

        popen = mock_popen.return_value
        popen.communicate.return_value = (mock_out, mock_err) = ("OUT_MSG", "")
        popen.returncode = mock_ret = 0

        # valid nodes
        for node in ('m3', 'gwt', 'a8'):
            ret, out, err = reset.reset(node)

        # invalid nodes
        try:
            node = 'INEXISTANT_ NODE'
            ret, out, err = reset.reset(node)
        except:
            pass
        else:
            assert 0, 'Non existant node not detected'


    def test_reset_OK(self, mock_popen):
        """
        successfull reset
        """
        # config mock
        popen = mock_popen.return_value
        popen.returncode = mock_ret = 0
        popen.communicate.return_value = \
                (mock_out, mock_err) = ("OUT_MSG", "")

        ret, out, err = reset.reset('m3')

        assert popen.communicate.call_count == 1
        assert mock_out == out
        assert mock_err == err
        assert mock_ret == ret


    def test_reset_Error(self, mock_popen):
        """
        Test with a reset with a unsuccessfull call
        """

        popen = mock_popen.return_value
        popen.returncode = mock_ret = 42
        popen.communicate.return_value = \
                (mock_out, mock_err) = ("OUT_ERR", "ERR_ERR")

        filename = 'TEST_FILENAME'
        ret, out, err = reset.reset('m3')

        assert popen.communicate.call_count == 1
        assert mock_out == out
        assert mock_err == err
        assert mock_ret == ret





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
            ret = reset.main(['reset.py'])
        except SystemExit as ret:
            assert ret.code != 0
        else:
            assert 0


    def test_error_help(self):
        """
        Running command line with --help
        """
        try:
            ret = reset.main(['reset.py', '-h'])
        except SystemExit as ret:
            assert ret.code == 0
        else:
            assert 0




    @mock.patch('gateway_code.reset.reset')
    def test_normal_run(self, mock_fct):
        """
        Running command line with m3
        """
        mock_fct.return_value = (0, 'OUTMessage', 'ErrorRunMessage')
        try:
            ret = reset.main(['reset.py', 'm3'])
        except SystemExit, ret:
            assert 0
        else:
            assert re.search('OK', captured_err.getvalue())
            assert ret == 0
        assert mock_fct.called


    @mock.patch('gateway_code.reset.reset')
    def test_error_run(self, mock_fct):
        """
        Running command line with error during run
        """
        mock_fct.return_value = (42, 'OUT', 'ErrorRunMessage')
        try:
            ret = reset.main(['reset.py', 'm3'])
        except SystemExit, ret:
            assert 0
        else:
            err = captured_err.getvalue()
            assert ret == 42
        assert mock_fct.called



