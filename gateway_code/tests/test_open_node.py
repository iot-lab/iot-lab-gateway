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

    @staticmethod
    @patch('gateway_code.autotest.expect.SerialExpect')
    def test__debug_boot_start_thread(expect_class):
        """ Run both cases for coverage """
        serial_expect = expect_class.return_value
        serial_expect.expect.return_value = ''

        a8_node = open_node.NodeA8(None)

        serial_expect.expect.return_value = ''
        a8_node._debug_boot_start(0)

        serial_expect.expect.return_value = ' login: '
        a8_node._debug_boot_start(0)

    @staticmethod
    def test_error_cases():
        """ Coverage cases execution """
        a8_node = open_node.NodeA8(None)
        a8_node._debug_boot_stop()
