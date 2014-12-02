# -*- coding:utf-8 -*-

""" expect module test """

import unittest
import mock
import time

from gateway_code.autotest import expect
import serial

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

        self.expect = expect.SerialExpect('TTY', 1234)

        self.read_ret = []

    def tearDown(self):
        self.serial_patcher.stop()

    def serial_read_mock(self, size):  # pylint:disable=unused-argument
        try:
            return self.read_ret.pop(0)
        except IndexError:
            time.sleep(0.1)
            return ''

    def test_run_init_and_del(self):
        self.serial_class.assert_called_with('TTY', 1234, timeout=0.1)
        del self.expect

    def test_send(self):
        self.expect.send('a_command')
        self.serial.write.assert_called_with('a_command\n')

    def test_expect(self):
        self.read_ret = ['abcde12345']
        ret = self.expect.expect('ab.*45')
        self.assertEquals('abcde12345', ret)

    def test_expect_timeout(self):
        self.read_ret = ['wrong_text']
        ret = self.expect.expect('ab.*45', 0.0)
        self.assertEquals('', ret)  # timeout

    def test_expect_on_multiple_reads(self):
        self.read_ret = ['a234567890123456', '', 'b234567890123456', '123456c']
        expected_ret = ''.join(self.read_ret)

        ret = self.expect.expect('a.*c')
        self.assertEquals(expected_ret, ret)

    def test_expect_list(self):
        self.read_ret = ['aaaa']
        ret = self.expect.expect_list(['a', 'b'])
        self.assertEquals('a', ret)

        self.read_ret = ['b']
        ret = self.expect.expect_list(['a', 'b'])
        self.assertEquals('b', ret)

    def test_expect_read_new_line(self):
        self.read_ret = ['ab\ncd', 'a00d']
        ret = self.expect.expect('a.*d')
        self.assertEquals('a00d', ret)

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
        self.assertEquals('', ret)

    def test_verbose_mode(self):
        logger = mock.Mock()
        logger.debug = mock.Mock(side_effet=ValueError(""))
        self.expect = expect.SerialExpect('TTY', 1234, logger=logger)

        self.read_ret = ['123\n456', '789\n', 'abcd']
        ret = self.expect.expect('a.*d')
        self.assertEquals(ret, 'abcd')

        logger.debug.assert_any_call('123')
        logger.debug.assert_any_call('456789')
        logger.debug.assert_called_with('abcd')
