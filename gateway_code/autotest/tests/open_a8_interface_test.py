# -*- coding:utf-8 -*-
# pylint: disable=missing-docstring
# pylint <= 1.3
# pylint: disable=too-many-public-methods
# pylint >= 1.4
# pylint: disable=too-few-public-methods
# pylint: disable=no-member

import unittest
from gateway_code.autotest import open_a8_interface


class TestA8ConnectionError(unittest.TestCase):
    def test_connection_error(self):
        error = open_a8_interface.A8ConnectionError("value", "err_msg")
        self.assertEquals("'value' : 'err_msg'", str(error))
