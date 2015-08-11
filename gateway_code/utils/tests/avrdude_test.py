# -*- coding:utf-8 -*-

# pylint: disable=missing-docstring
# pylint: disable=too-many-public-methods
# pylint: disable=invalid-name
# pylint: disable=protected-access
# serial mock note correctly detected
# pylint: disable=maybe-no-member
# pylint: disable=unused-argument

import os.path
import mock
import unittest
import serial

from .. import avrdude
from gateway_code.open_node import NodeLeonardo  # config file


class TestsMethods(unittest.TestCase):

    """ Tests avrdude methods """

    def setUp(self):
        self.avr = avrdude.AvrDude(NodeLeonardo.AVRDUDE_CONF)

    @mock.patch('subprocess.call')
    def test_flash(self, call_mock):
        """ Test flash """
        call_mock.return_value = 0
        ret = self.avr.flash(NodeLeonardo.FW_IDLE)
        self.assertEquals(0, ret)

        call_mock.return_value = 42
        ret = self.avr.flash(NodeLeonardo.FW_IDLE)
        self.assertEquals(42, ret)

    def test_invalid_firmware_path(self):
        ret = self.avr.flash('/invalid/path')
        self.assertNotEqual(0, ret)


@mock.patch('serial.Serial')
class TestTriggerBootloader(unittest.TestCase):
    """ Test the 'trigger_bootloader' function """

    def setUp(self):
        self.tty = '/tmp/test_trigger_tty'
        self.tty_prog = '/tmp/test_trigger_tty_prog'
        self._del_tty_prog()

    def teardown(self):
        self._del_tty_prog()

    def _create_tty_prog(self, *_, **__):
        self.assertFalse(os.path.exists(self.tty_prog))
        open(self.tty_prog, 'a').close()
        return mock.DEFAULT

    def _del_tty_prog(self, *_, **__):
        try:
            os.remove(self.tty_prog)
        except OSError:
            pass
        return mock.DEFAULT

    def test_trigger(self, serial_mock):
        """ Opening self.tty should create the 'prog' tty """
        serial_mock.side_effect = self._create_tty_prog

        ret = avrdude.AvrDude.trigger_bootloader(self.tty, self.tty_prog,
                                                 timeout=2)
        self.assertEquals(0, ret)
        self.assertTrue(os.path.exists(self.tty_prog))

    def test_trigger_fail(self, serial_mock):
        """ Opening self.tty will not create the 'prog' tty """
        serial_mock.side_effect = self._del_tty_prog

        ret = avrdude.AvrDude.trigger_bootloader(self.tty, self.tty_prog,
                                                 timeout=1)
        self.assertNotEquals(0, ret)
        self.assertFalse(os.path.exists(self.tty_prog))

    def test_error_opening_tty(self, serial_mock):
        """ Test Error handling while opening the trigger tty """
        serial_mock.side_effect = serial.SerialException('Test Error')
        ret = avrdude.AvrDude.trigger_bootloader(self.tty, self.tty_prog)
        self.assertNotEqual(0, ret)

        serial_mock.side_effect = OSError()
        ret = avrdude.AvrDude.trigger_bootloader(self.tty, self.tty_prog)
        self.assertNotEqual(0, ret)
