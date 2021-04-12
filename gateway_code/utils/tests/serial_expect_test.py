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


""" expect module test """

import time
import unittest

import serial
import mock

from .. import serial_expect

# pylint: disable=missing-docstring
# pylint <= 1.3
# pylint: disable=too-many-public-methods
# pylint >= 1.4
# pylint: disable=too-few-public-methods
# pylint: disable=no-member


class TestSerialExpect(unittest.TestCase):

    def setUp(self):

        self.serial_patcher = mock.patch('serial.Serial')
        self.serial_class = self.serial_patcher.start()
        self.serial = self.serial_class.return_value
        self.serial.read = self.serial_read_mock

        self.expect = serial_expect.SerialExpect('TTY', 1234)

        self.read_ret = []

    def tearDown(self):
        self.serial_patcher.stop()

    def serial_read_mock(self, size):  # pylint:disable=unused-argument
        try:
            return self.read_ret.pop(0)
        except IndexError:
            time.sleep(0.1)
            return b''

    def test_run_init_and_del(self):
        self.serial_class.assert_called_with('TTY', 1234, timeout=0.1)
        del self.expect

    def test_send(self):
        self.expect.send('a_command')
        self.serial.write.assert_called_with(b'a_command\n')

    def test_expect(self):
        self.read_ret = [b'abcde12345']
        ret = self.expect.expect('ab.*45')
        self.assertEqual('abcde12345', ret)

    def test_expect_empty(self):
        self.read_ret = []
        assert self.serial.read(1) == b''

    def test_expect_timeout(self):
        self.read_ret = [b'wrong_text']
        ret = self.expect.expect('ab.*45', 0.0)
        self.assertEqual('', ret)  # timeout

    def test_expect_on_multiple_reads(self):
        self.read_ret = [b'a234567890123456', b'', b'b234567890123456',
                         b'123456c']
        expected_ret = (b''.join(self.read_ret)).decode()

        ret = self.expect.expect('a.*c')
        self.assertEqual(expected_ret, ret)

    def test_expect_list(self):
        self.read_ret = [b'aaaa']
        ret = self.expect.expect_list(['a', 'b'])
        self.assertEqual('a', ret)

        self.read_ret = [b'b']
        ret = self.expect.expect_list(['a', 'b'])
        self.assertEqual('b', ret)

    def test_expect_read_new_line(self):
        self.read_ret = [b'ab\ncd', b'a00d']
        ret = self.expect.expect('a.*d')
        self.assertEqual('a00d', ret)

    def test_expect_newline_pattern(self):
        self.assertRaises(ValueError, self.expect.expect, 'abc\rdef\nghi')

    def test_expect_list_parameters(self):
        expect_mock = mock.Mock(return_value='')
        self.expect.expect = expect_mock

        self.expect.expect_list(['.*'], 0.3)
        expect_mock.assert_called_with('(.*)', 0.3)

        self.expect.expect_list(['a', 'b', 'c'])
        expect_mock.assert_called_with('(a)|(b)|(c)', float('+inf'))

    def test_read_a_closed_serial(self):
        self.serial.read = mock.Mock(side_effect=serial.SerialException(
            "FD already closed"))
        ret = self.expect.expect('a.*d')
        self.assertEqual('', ret)

    def test_close_attribute_error(self):
        # Smoke test for close when and AttributeError exception is raised.
        self.serial.close = mock.Mock(side_effect=AttributeError)
        self.expect.close()

    def test_verbose_mode(self):
        logger = mock.Mock()
        logger.debug = mock.Mock(side_effet=ValueError(""))
        self.expect = serial_expect.SerialExpect('TTY', 1234, logger=logger)

        self.read_ret = [b'123\n456', b'789\n', b'abcd']
        ret = self.expect.expect('a.*d')
        self.assertEqual(ret, 'abcd')

        logger.debug.assert_any_call('123')
        logger.debug.assert_any_call('456789')
        logger.debug.assert_called_with('abcd')

    def test_context_manager(self):
        with serial_expect.SerialExpect('TTY', 1234) as ser:
            self.read_ret = [b'123\n456', b'789\n', b'abcd']
            ret = ser.expect('a.*d')
            self.assertEqual(ret, 'abcd')
