# -*- coding:utf-8 -*-

""" Test gateway_code.open_node module """

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=too-many-public-methods

import unittest
from mock import patch
import gateway_code.open_node as open_node


class TestNodeA8(unittest.TestCase):
    def test_wait_tty(self):
        """ Test running wait_tty fct """
        self.assertEquals(0, open_node.wait_tty('/dev/null'))
        self.assertNotEquals(0, open_node.wait_tty('no_tty_file'))

    @staticmethod
    @patch('gateway_code.autotest.expect.SerialExpect')
    def test__debug_a8_boot_start_thread(expect_class):
        """ Run both cases for coverage """
        serial_expect = expect_class.return_value
        serial_expect.expect.return_value = ''

        a8_node = open_node.NodeA8(None)

        serial_expect.expect.return_value = ''
        a8_node._debug_a8_boot_start_thread(0, {})

        serial_expect.expect.return_value = ' login: '
        a8_node._debug_a8_boot_start_thread(0, {})

    @staticmethod
    def test_error_cases():
        """ Coverage cases execution """
        a8_node = open_node.NodeA8(None)
        a8_node._debug_a8_boot_stop_thread()
