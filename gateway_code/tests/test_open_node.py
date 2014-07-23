# -*- coding:utf-8 -*-

""" Test gateway_code.open_node module """

import unittest
from mock import patch
import gateway_code.open_node as open_node


class TestNodeA8(unittest.TestCase):
    def test_wait_tty_a8(self):
        """ Test running wait_tty_a8 fct """
        self.assertEquals(0, open_node.NodeA8.wait_tty_a8('/dev/null'))
        self.assertNotEquals(0, open_node.NodeA8.wait_tty_a8('no_tty_file'))

    @patch('gateway_code.autotest.expect.SerialExpect')
    def test__debug_a8_boot_start_thread(self, expect_class):
        """ Run both cases for coverage """
        serial_expect = expect_class.return_value
        serial_expect.expect.return_value = ''

        a8_node = open_node.NodeA8(None)

        serial_expect.expect.return_value = ''
        a8_node._debug_a8_boot_start_thread(0, {})

        serial_expect.expect.return_value = ' login: '
        a8_node._debug_a8_boot_start_thread(0, {})

    def test_error_cases(self):
        """ Coverage cases execution """
        a8_node = open_node.NodeA8(None)
        a8_node._debug_a8_boot_stop_thread()
