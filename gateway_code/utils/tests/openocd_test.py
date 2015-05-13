#! /usr/bin/env python
# -*- coding:utf-8 -*-

# pylint: disable=missing-docstring
# pylint: disable=too-many-public-methods
# pylint: disable=invalid-name
# pylint: disable=protected-access
# serial mock note correctly detected
# pylint: disable=maybe-no-member

import sys
import unittest
from mock import patch

from .. import openocd
from gateway_code.open_node import NodeM3


@patch('subprocess.call')
class TestsMethods(unittest.TestCase):
    """ Tests openocd methods """

    def test_flash(self, call_mock):
        """ Test flash """
        call_mock.return_value = 0
        ret = openocd.flash(NodeM3.OPENOCD_CFG_FILE, NodeM3.FW_IDLE)
        self.assertEquals(0, ret)

        call_mock.return_value = 42
        ret = openocd.flash(NodeM3.OPENOCD_CFG_FILE, NodeM3.FW_IDLE)
        self.assertEquals(42, ret)

    def test_reset(self, call_mock):
        """ Test reset"""
        call_mock.return_value = 0
        ret = openocd.reset(NodeM3.OPENOCD_CFG_FILE)
        self.assertEquals(0, ret)

        call_mock.return_value = 42
        ret = openocd.reset(NodeM3.OPENOCD_CFG_FILE)
        self.assertEquals(42, ret)


class TestsFlashInvalidPaths(unittest.TestCase):
    def test_invalid_config_file_path(self):
        self.assertRaises(IOError, openocd.flash,
                          '/invalid/path', '/dev/null')

    def test_invalid_firmware_path(self):
        ret = openocd.flash(NodeM3.OPENOCD_CFG_FILE, '/invalid/path')
        self.assertNotEqual(0, ret)


# Command line tests
@patch('sys.stderr', sys.stdout)
class TestsCommandLineCalls(unittest.TestCase):

    @patch('gateway_code.utils.openocd.flash')
    def test_flash(self, mock_fct):
        """ Running command line flash """
        mock_fct.return_value = 0
        ret = openocd._main(['openocd.py', 'flash', 'M3', '/dev/null'])
        self.assertEquals(ret, 0)

        mock_fct.return_value = 42
        ret = openocd._main(['openocd.py', 'flash', 'M3', '/dev/null'])
        self.assertEquals(ret, 42)

    @patch('gateway_code.utils.openocd.reset')
    def test_reset(self, mock_fct):
        """ Running command line reset """
        mock_fct.return_value = 0
        ret = openocd._main(['openocd.py', 'reset', 'M3'])
        self.assertEquals(ret, 0)

        mock_fct.return_value = 42
        ret = openocd._main(['openocd.py', 'reset', 'M3'])
        self.assertEquals(ret, 42)
