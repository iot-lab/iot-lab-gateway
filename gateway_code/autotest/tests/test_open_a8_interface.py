# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring
# pylint: disable=too-many-public-methods

import unittest
from gateway_code.autotest import open_a8_interface


class TestA8ConnectionError(unittest.TestCase):
    def test_connection_error(self):
        error = open_a8_interface.A8ConnectionError("value", "err_msg")
        self.assertEquals("'value' : 'err_msg'", str(error))
