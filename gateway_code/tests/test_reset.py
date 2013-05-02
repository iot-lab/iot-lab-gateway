#! /usr/bin/env python

import unittest
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
class TestsResetMethods(unittest.TestCase):
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
        node = 'INEXISTANT_ NODE'
        self.assertRaises(ValueError, reset.reset, node)


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

        self.assertEquals(popen.communicate.call_count, 1)
        self.assertEquals((ret, out, err), (mock_ret, mock_out, mock_err))


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

        self.assertEquals(popen.communicate.call_count, 1)
        self.assertEquals((ret, out, err), (mock_ret, mock_out, mock_err))





# Command line tests

from cStringIO import StringIO
captured_out = StringIO()
captured_err = StringIO()
@mock.patch('sys.stdout', captured_out)
@mock.patch('sys.stderr', captured_err)
class TestsCommandLineCalls(unittest.TestCase):

    @mock.patch('gateway_code.reset.reset')
    def test_normal_run(self, mock_fct):
        """
        Running command line with m3
        """
        mock_fct.return_value = (0, 'OUTMessage', 'ErrorRunMessage')
        ret = reset.main(['reset.py', 'm3'])

        self.assertEquals(ret, 0)
        self.assertTrue(mock_fct.called)


    @mock.patch('gateway_code.reset.reset')
    def test_error_run(self, mock_fct):
        """
        Running command line with error during run
        """
        mock_fct.return_value = (42, 'OUT', 'ErrorRunMessage')
        ret = reset.main(['reset.py', 'm3'])

        self.assertEquals(ret, 42)
        self.assertTrue(mock_fct.called)



