# -*- coding:utf-8 -*-

# This file is a part of IoT-LAB gateway_code
# Copyright (C) 2015 INRIA (Contact: admin@iot-lab.info)
# Contributor(s) : see AUTHORS file
#
# This software is governed by the CeCILL license under French law
# and abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# http://www.cecill.info.
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.


# pylint: disable=missing-docstring
# pylint: disable=too-many-public-methods
# pylint: disable=invalid-name
# pylint: disable=protected-access
# serial mock note correctly detected
# pylint: disable=maybe-no-member
# pylint: disable=unused-argument

import time
import os.path
import unittest

import serial
import mock

from gateway_code.open_nodes.node_leonardo import NodeLeonardo
from gateway_code.open_nodes.node_atmega256rfr2 import NodeAtmega256rfr2
from .. import avrdude


class TestsMethods(unittest.TestCase):
    """Tests avrdude methods."""

    def setUp(self):
        self.avr = avrdude.AvrDude(NodeLeonardo.AVRDUDE_CONF)

    @mock.patch('gateway_code.utils.subprocess_timeout.call')
    def test_flash(self, call_mock):
        """Test flash."""
        call_mock.return_value = 0
        ret = self.avr.flash(NodeLeonardo.FW_IDLE)
        self.assertEqual(0, ret)
        assert 'atmega32u4' in call_mock.call_args.kwargs['args']
        assert 'avr109' in call_mock.call_args.kwargs['args']
        assert NodeLeonardo.TTY_PROG in call_mock.call_args.kwargs['args']
        assert '-D' in call_mock.call_args.kwargs['args']

        call_mock.return_value = 42
        ret = self.avr.flash(NodeLeonardo.FW_IDLE)
        self.assertEqual(42, ret)

    def test_invalid_firmware_path(self):
        ret = self.avr.flash('/invalid/path')
        self.assertNotEqual(0, ret)


class TestsCall(unittest.TestCase):
    """ Tests avrdude call timeout """
    def setUp(self):
        self.timeout = 5
        self.avr = avrdude.AvrDude(NodeLeonardo.AVRDUDE_CONF,
                                   timeout=self.timeout)
        self.avr._avrdude_args = mock.Mock()

    def test_timeout_call(self):
        """Test timeout reached."""
        self.avr._avrdude_args.return_value = {'args': ['sleep', '10']}
        t_0 = time.time()
        ret = self.avr._call_cmd('sleep')
        t_end = time.time()

        # Not to much more
        self.assertLess(t_end - t_0, self.timeout + 1)
        self.assertNotEqual(ret, 0)

    def test_no_timeout(self):
        """Test timeout not reached."""
        self.avr._avrdude_args.return_value = {'args': ['sleep', '1']}
        t_0 = time.time()
        ret = self.avr._call_cmd('sleep')
        t_end = time.time()

        # Strictly lower here
        self.assertLess(t_end - t_0, self.timeout - 1)
        self.assertEqual(ret, 0)


@mock.patch('serial.Serial')
class TestTriggerBootloader(unittest.TestCase):
    """Test 'trigger_bootloader' function."""

    def setUp(self):
        self.tty = '/tmp/test_trigger_tty'
        self.tty_prog = '/tmp/test_trigger_tty_prog'
        self._del_tty_prog()

    def tearDown(self):
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
        """Opening self.tty should create the 'prog' tty."""
        serial_mock.side_effect = self._create_tty_prog

        ret = avrdude.AvrDude.trigger_bootloader(self.tty, self.tty_prog,
                                                 timeout=2)
        self.assertEqual(0, ret)
        self.assertTrue(os.path.exists(self.tty_prog))

    def test_trigger_fail(self, serial_mock):
        """Opening self.tty will not create the 'prog' tty."""
        serial_mock.side_effect = self._del_tty_prog

        ret = avrdude.AvrDude.trigger_bootloader(self.tty, self.tty_prog,
                                                 timeout=1)
        self.assertNotEqual(0, ret)
        self.assertFalse(os.path.exists(self.tty_prog))

    def test_serial_error_opening_tty(self, serial_mock):
        """Test SerialError handling while opening the trigger tty."""
        serial_mock.side_effect = serial.SerialException('Test Error')
        ret = avrdude.AvrDude.trigger_bootloader(self.tty, self.tty_prog)
        self.assertNotEqual(0, ret)

    def test_oserror_opening_tty(self, serial_mock):
        """Test OSError handling while opening the trigger tty."""
        serial_mock.side_effect = OSError()
        ret = avrdude.AvrDude.trigger_bootloader(self.tty, self.tty_prog)
        self.assertNotEqual(0, ret)


class TestsXplainedMethods(unittest.TestCase):
    """Tests avrdude methods used with xplained programmer."""

    def setUp(self):
        self.avr = avrdude.AvrDude(NodeAtmega256rfr2.AVRDUDE_CONF)

    @mock.patch('gateway_code.utils.subprocess_timeout.call')
    def test_flash(self, call_mock):
        """Test flash."""
        call_mock.return_value = 0
        ret = self.avr.flash(NodeAtmega256rfr2.FW_IDLE)
        self.assertEqual(0, ret)
        assert 'm256rfr2' in call_mock.call_args.kwargs['args']
        assert 'xplainedpro' in call_mock.call_args.kwargs['args']
        assert 'tty' not in call_mock.call_args.kwargs['args']
        assert '-D' not in call_mock.call_args.kwargs['args']
        assert call_mock.call_args.kwargs['args'][-1].startswith('flash:w:')

        call_mock.return_value = 42
        ret = self.avr.flash(NodeAtmega256rfr2.FW_IDLE)
        self.assertEqual(42, ret)

    @mock.patch('gateway_code.utils.subprocess_timeout.call')
    def test_reset(self, call_mock):
        call_mock.return_value = 0
        ret = self.avr.reset()
        self.assertEqual(0, ret)
        assert 'm256rfr2' in call_mock.call_args.kwargs['args']
        assert 'xplainedpro' in call_mock.call_args.kwargs['args']
        assert NodeAtmega256rfr2.TTY not in call_mock.call_args.kwargs['args']
