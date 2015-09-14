# -*- coding:utf-8 -*-

# pylint: disable=missing-docstring
# pylint: disable=too-many-public-methods
# pylint: disable=invalid-name
# pylint: disable=protected-access
# serial mock note correctly detected
# pylint: disable=maybe-no-member

import mock
import unittest

from .. import openocd
from gateway_code.open_nodes.node_m3 import NodeM3  # config file


@mock.patch('subprocess.call')
class TestsMethods(unittest.TestCase):
    """ Tests openocd methods """
    def setUp(self):
        self.ocd = openocd.OpenOCD(NodeM3.OPENOCD_CFG_FILE)

    def test_flash(self, call_mock):
        """ Test flash """
        call_mock.return_value = 0
        ret = self.ocd.flash(NodeM3.FW_IDLE)
        self.assertEquals(0, ret)

        call_mock.return_value = 42
        ret = self.ocd.flash(NodeM3.FW_IDLE)
        self.assertEquals(42, ret)

    def test_reset(self, call_mock):
        """ Test reset"""
        call_mock.return_value = 0
        ret = self.ocd.reset()
        self.assertEquals(0, ret)

        call_mock.return_value = 42
        ret = self.ocd.reset()
        self.assertEquals(42, ret)


class TestsFlashInvalidPaths(unittest.TestCase):
    def test_invalid_config_file_path(self):
        self.assertRaises(IOError, openocd.OpenOCD, '/invalid/path')

    def test_invalid_firmware_path(self):
        ret = openocd.OpenOCD(NodeM3.OPENOCD_CFG_FILE).flash('/invalid/path')
        self.assertNotEqual(0, ret)
