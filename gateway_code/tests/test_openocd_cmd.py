#! /usr/bin/env python
# -*- coding:utf-8 -*-

# pylint: disable=missing-docstring
# pylint: disable=too-many-public-methods
# pylint: disable=invalid-name
# pylint: disable=protected-access
# serial mock note correctly detected
# pylint: disable=maybe-no-member

from mock import patch
import unittest
from cStringIO import StringIO

from os.path import dirname, abspath

from gateway_code import openocd_cmd

CURRENT_DIR = dirname(abspath(__file__)) + '/'
STATIC_DIR = CURRENT_DIR + 'static/'  # using the 'static' symbolic link


@patch('gateway_code.config.STATIC_FILES_PATH', new=STATIC_DIR)
class TestsFlashMethods(unittest.TestCase):
    """
    Tests flash_firmware methods
    """
    def setUp(self):
        self.popen_patcher = patch('subprocess.Popen')
        popen_class_mock = self.popen_patcher.start()
        self.popen = popen_class_mock.return_value

    def tearDown(self):
        self.popen_patcher.stop()

    def test_node_detection(self):
        """ Test node detection """
        # config mock
        self.popen.communicate.return_value = "OUT_MSG"
        self.popen.returncode = 0

        # valid nodes
        for node in ('m3', 'gwt', 'a8'):
            filename = STATIC_DIR + 'idle.elf'
            openocd_cmd.flash(node, filename)

        # invalid nodes
        self.assertRaises(ValueError, openocd_cmd.flash, 'INEXISTANT',
                          '/dev/null')

    def test_flash_OK(self):
        """ Test with a flash with a successfull call """
        # config mock
        self.popen.communicate.return_value = mock_out = "OUT_MSG"
        self.popen.returncode = mock_ret = 0

        filename = STATIC_DIR + 'idle.elf'
        ret, out = openocd_cmd.flash('m3', filename)

        self.assertEquals(self.popen.communicate.call_count, 1)
        self.assertEquals((ret, out), (mock_ret, mock_out))

    def test_flash_Error(self):
        """ Test with a flash with a unsuccessfull call """
        self.popen.returncode = mock_ret = 42
        self.popen.communicate.return_value = mock_out = "OUT_ERR"

        filename = STATIC_DIR + 'idle.elf'
        ret, out = openocd_cmd.flash('m3', filename)

        self.assertEquals(self.popen.communicate.call_count, 1)
        self.assertEquals((ret, out), (mock_ret, mock_out))


class TestsFlashInvalidPaths(unittest.TestCase):
    @patch('gateway_code.config.STATIC_FILES_PATH', new='/invalid/path/')
    def test_invalid_config_file_path(self):
        self.assertRaises(IOError, openocd_cmd.flash, 'm3', '/dev/null')

    @patch('gateway_code.config.STATIC_FILES_PATH', new=STATIC_DIR)
    def test_invalid_firmware_path(self):
        ret, _ = openocd_cmd.flash('m3', '/invalid/path')
        self.assertNotEqual(ret, 0)


@patch('gateway_code.config.STATIC_FILES_PATH', new=STATIC_DIR)
class TestsResetMethods(unittest.TestCase):
    """ Tests reset functions """
    def setUp(self):
        self.popen_patcher = patch('subprocess.Popen')
        popen_class_mock = self.popen_patcher.start()
        self.popen = popen_class_mock.return_value

    def tearDown(self):
        self.popen_patcher.stop()

    def test_reset_OK(self):
        """ successfull reset """
        # config mock
        self.popen.communicate.return_value = mock_out = "OUT_MSG"
        self.popen.returncode = mock_ret = 0

        ret, out = openocd_cmd.reset('m3')

        self.assertEquals(self.popen.communicate.call_count, 1)
        self.assertEquals((ret, out), (mock_ret, mock_out))

    def test_reset_Error(self):
        """ Test with a reset with a unsuccessfull call """
        self.popen.communicate.return_value = mock_out = "OUT_MSG"
        self.popen.returncode = mock_ret = 42

        ret, out = openocd_cmd.reset('m3')

        self.assertEquals(self.popen.communicate.call_count, 1)
        self.assertEquals((ret, out), (mock_ret, mock_out))


# Command line tests
@patch('sys.stderr', StringIO())
@patch('gateway_code.openocd_cmd.flash')
class TestsCommandLineCallsFlash(unittest.TestCase):

    def test_normal_run(self, mock_fct):
        """ Running command line with m3 """
        mock_fct.return_value = (0, 'OUTMessage')
        ret = openocd_cmd._main(['openocd_cmd.py', 'flash', 'm3', '/dev/null'])

        self.assertEquals(ret, 0)
        self.assertTrue(mock_fct.called)

    def test_error_run(self, mock_fct):
        """ Running command line with error during run """

        mock_fct.return_value = (42, 'OUT')
        ret = openocd_cmd._main(['openocd_cmd.py', 'flash', 'm3', '/dev/null'])

        self.assertEquals(ret, 42)
        self.assertTrue(mock_fct.called)


# Command line tests
@patch('sys.stderr', StringIO())
@patch('gateway_code.openocd_cmd.reset')
class TestsCommandLineCallsReset(unittest.TestCase):

    def test_normal_run(self, mock_fct):
        """
        Running command line with m3
        """
        mock_fct.return_value = (0, 'OUTMessage')
        ret = openocd_cmd._main(['openocd_cmd.py', 'reset', 'm3'])

        self.assertEquals(ret, 0)
        self.assertTrue(mock_fct.called)

    def test_error_run(self, mock_fct):
        """
        Running command line with error during run
        """
        mock_fct.return_value = (42, 'OUT')
        ret = openocd_cmd._main(['openocd_cmd.py', 'reset', 'm3'])

        self.assertEquals(ret, 42)
        self.assertTrue(mock_fct.called)
