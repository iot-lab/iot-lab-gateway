#! /usr/bin/env python


import sys

import mock
import unittest
from cStringIO import StringIO

from os.path import dirname, abspath

import gateway_code
from gateway_code import flash_firmware

CURRENT_DIR = dirname(abspath(__file__)) + '/'
STATIC_DIR  = CURRENT_DIR + 'static/' # using the 'static' symbolic link

from subprocess import PIPE
@mock.patch('gateway_code.flash_firmware.config.STATIC_FILES_PATH', new=STATIC_DIR)
class TestsFlashMethods(unittest.TestCase):
    """
    Tests flash_firmware methods
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
        self.popen.returncode = mock_ret = 0

        # valid nodes
        for node in ('m3', 'gwt', 'a8'):
            filename = STATIC_DIR + 'idle.elf'
            ret, out, err = flash_firmware.flash(node, filename)

        # invalid nodes
        self.assertRaises(ValueError, flash_firmware.flash, 'INEXISTANT', '/dev/null')


    def test_flash_OK(self):
        """
        Test with a flash with a successfull call
        """

        # config mock
        self.popen.communicate.return_value = (mock_out, mock_err) = ("OUT_MSG", "")
        self.popen.returncode = mock_ret = 0

        filename = STATIC_DIR + 'idle.elf'
        ret, out, err = flash_firmware.flash('m3', filename)

        self.assertEquals(self.popen.communicate.call_count, 1)
        self.assertEquals((ret, out, err), (mock_ret, mock_out, mock_err))


    def test_flash_Error(self):
        """
        Test with a flash with a unsuccessfull call
        """
        self.popen.returncode = mock_ret = 42
        self.popen.communicate.return_value = \
                (mock_out, mock_err) = ("OUT_ERR", "ERR_ERR")

        filename = STATIC_DIR + 'idle.elf'
        ret, out, err = flash_firmware.flash('m3', filename)

        self.assertEquals(self.popen.communicate.call_count, 1)
        self.assertEquals((ret, out, err), (mock_ret, mock_out, mock_err))


class TestsFlashInvalidPaths(unittest.TestCase):
    @mock.patch('gateway_code.reset.config.STATIC_FILES_PATH', new='/invalid/path/')
    def test_invalid_config_file_path(self):
        self.assertRaises(OSError, flash_firmware.flash, 'm3', '/dev/null')

    @mock.patch('gateway_code.flash_firmware.config.STATIC_FILES_PATH', new=STATIC_DIR)
    def test_invalid_firmware_path(self):
        ret, out, err = flash_firmware.flash('m3', '/invalid/path')
        self.assertNotEqual(ret, 0)




# Command line tests

from cStringIO import StringIO
captured_err = StringIO()
@mock.patch('sys.stderr', captured_err)
class TestsCommandLineCalls(unittest.TestCase):

    def test_simple_args(self):
        """ Running command line without arguments """
        self.assertRaises(SystemExit, flash_firmware.main, ['flash_firmware.py'])
        self.assertRaises(SystemExit, flash_firmware.main, ['flash_firmware.py', '-h'])


    @mock.patch('gateway_code.flash_firmware.flash')
    def test_normal_run(self, mock_fct):
        """ Running command line with m3 """
        mock_fct.return_value = (0, 'OUTMessage', 'ErrorRunMessage')
        ret = flash_firmware.main(['flash_firmware.py', 'm3', '/dev/null'])

        self.assertEquals(ret, 0)
        self.assertTrue(mock_fct.called)


    @mock.patch('gateway_code.flash_firmware.flash')
    def test_error_run(self, mock_fct):
        """ Running command line with error during run """

        mock_fct.return_value = (42, 'OUT', 'ErrorRunMessage')
        ret = flash_firmware.main(['flash_firmware.py', 'm3', '/dev/null'])

        self.assertEquals(ret, 42)
        self.assertTrue(mock_fct.called)


