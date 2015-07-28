# -*- coding:utf-8 -*-

""" Test gateway_code.open_node module """

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=too-many-public-methods

import unittest
from mock import patch

from gateway_code.open_nodes.node_a8 import NodeA8


class TestNodeA8(unittest.TestCase):

    @patch('gateway_code.open_nodes.node_a8.SerialExpect')
    def test__debug_boot_thread(self, expect_class):
        """ Run both cases for coverage """
        serial_expect = expect_class.return_value

        a8_node = NodeA8()

        serial_expect.expect.return_value = ''
        ret = a8_node._debug_thread(0)
        self.assertEquals(ret, '')

        serial_expect.expect.return_value = ' login: '
        ret = a8_node._debug_thread(0)
        self.assertIn('login:', ret)

    @staticmethod
    def test_error_cases():
        """ Coverage cases execution """
        a8_node = NodeA8()
        a8_node._debug_boot_stop()
