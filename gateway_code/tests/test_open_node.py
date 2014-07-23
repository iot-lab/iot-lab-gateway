# -*- coding:utf-8 -*-

""" Test gateway_code.open_node module """

import unittest
import gateway_code.open_node as open_node


class TestNodeA8(unittest.TestCase):
    def test_wait_tty_a8(self):
        """ Test running wait_tty_a8 fct """
        self.assertEquals(0, open_node.NodeA8.wait_tty_a8('/dev/null'))
        self.assertNotEquals(0, open_node.NodeA8.wait_tty_a8('no_tty_file'))
