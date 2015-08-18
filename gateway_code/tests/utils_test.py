# -*- coding: utf-8 -*-

# pylint: disable=missing-docstring

import unittest
from . import utils


class TestUtilsMock(unittest.TestCase):

    def test_read_config_mock(self):

        read_cfg = utils.read_config_mock('m3', test_key='value')
        self.assertEquals('m3', read_cfg('board_type'))

        # No robot by default
        self.assertRaises(IOError, read_cfg, 'robot')
        self.assertEquals(None, read_cfg('robot', None))

        # Extra key
        self.assertEquals('value', read_cfg('test_key'))
        self.assertEquals('value', read_cfg('test_key', 'default'))
