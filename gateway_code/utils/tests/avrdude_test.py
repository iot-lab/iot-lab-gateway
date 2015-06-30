# -*- coding:utf-8 -*-

# pylint: disable=missing-docstring
# pylint: disable=too-many-public-methods
# pylint: disable=invalid-name
# pylint: disable=protected-access
# serial mock note correctly detected
# pylint: disable=maybe-no-member
# pylint: disable=unused-argument

import mock
import unittest

from .. import avrdude
from gateway_code.open_node import NodeLeonardo  # config file


@mock.patch('subprocess.call')
class TestsMethods(unittest.TestCase):

    """ Tests avrdude methods """

    def setUp(self):
        self.avr = avrdude.AvrDude(
            NodeLeonardo.AVRDUDE_CFG_FILE, NodeLeonardo.TTY_PROG)

    def test_flash(self, call_mock):
        """ Test flash """
        call_mock.return_value = 0
        ret = self.avr.flash(NodeLeonardo.FW_IDLE)
        self.assertEquals(0, ret)

        call_mock.return_value = 42
        ret = self.avr.flash(NodeLeonardo.FW_IDLE)
        self.assertEquals(42, ret)

    @mock.patch('serial.Serial')
    @mock.patch('serial.Serial.close')
    def test_trigger(self, call_mock1, call_mock2, call_mock3):
        ret = 0
        ret = avrdude.AvrDude.trigger_bootloader('/dev/null', '/dev/null')
        self.assertEquals(0, ret)


class TestsFlashInvalidPaths(unittest.TestCase):

    def test_invalid_config_file_path(self):
        self.assertRaises(IOError, avrdude.AvrDude, '/invalid/path', 'NotATty')

    def test_invalid_firmware_path(self):
        ret = avrdude.AvrDude(
            NodeLeonardo.AVRDUDE_CFG_FILE, NodeLeonardo.TTY_PROG).flash(
                '/invalid/path')
        self.assertNotEqual(0, ret)

    def test_invalid_tty(self):
        ret = avrdude.AvrDude.trigger_bootloader('/dev/null', '/dev/null')
        self.assertNotEqual(0, ret)
