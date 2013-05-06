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

@mock.patch('gateway_code.reset.config.STATIC_FILES_PATH', new=STATIC_DIR)
class TestsResetMethods(unittest.TestCase):
    """
    Tests reset functions
    """
    def setUp(self):
        self.popen_patcher = mock.patch('subprocess.Popen')
        popen_class_mock = self.popen_patcher.start()
        self.popen = popen_class_mock.return_value

    def tearDown(self):
        self.popen_patcher.stop()


    def test_node_detection(self):
        """ Test node detection """
        # config mock

        self.popen.communicate.return_value = (mock_out, mock_err) = ("OUT_MSG", "")
        self.popen.returncode               = mock_ret             = 0

        # valid nodes
        for node in ('m3', 'gwt', 'a8'):
            ret, out, err = reset.reset(node)
            self.assertEquals(ret, mock_ret)

        # invalid nodes
        self.assertRaises(ValueError, reset.reset, 'INEXISTANT_NODE')


    def test_reset_OK(self):
        """
        successfull reset
        """
        # config mock
        self.popen.communicate.return_value = (mock_out, mock_err) = ("OUT_MSG", "")
        self.popen.returncode               = mock_ret             = 0

        ret, out, err = reset.reset('m3')

        self.assertEquals(self.popen.communicate.call_count, 1)
        self.assertEquals((ret, out, err), (mock_ret, mock_out, mock_err))


    def test_reset_Error(self):
        """
        Test with a reset with a unsuccessfull call
        """

        self.popen.communicate.return_value = (mock_out, mock_err) = ("OUT_ERR", "ERR_ERR")
        self.popen.returncode               = mock_ret             = 42

        ret, out, err = reset.reset('m3')

        self.assertEquals(self.popen.communicate.call_count, 1)
        self.assertEquals((ret, out, err), (mock_ret, mock_out, mock_err))

@mock.patch('gateway_code.reset.config.STATIC_FILES_PATH', new='/invalid/path/')
class TestsResetInvalidConfigFilePath(unittest.TestCase):
    def test_invalid_config_file_path(self):
        self.assertRaises(OSError, reset.reset, 'm3')




# Command line tests

from cStringIO import StringIO
captured_err = StringIO()
@mock.patch('sys.stderr', captured_err)
@mock.patch('gateway_code.reset.reset')
class TestsCommandLineCalls(unittest.TestCase):

    def test_normal_run(self, mock_fct):
        """
        Running command line with m3
        """
        mock_fct.return_value = (0, 'OUTMessage', 'ErrorRunMessage')
        ret = reset.main(['reset.py', 'm3'])

        self.assertEquals(ret, 0)
        self.assertTrue(mock_fct.called)


    def test_error_run(self, mock_fct):
        """
        Running command line with error during run
        """
        mock_fct.return_value = (42, 'OUT', 'ErrorRunMessage')
        ret = reset.main(['reset.py', 'm3'])

        self.assertEquals(ret, 42)
        self.assertTrue(mock_fct.called)



