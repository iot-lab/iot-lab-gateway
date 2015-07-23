#! /usr/bin/env python
# -*- coding:utf-8 -*-

# pylint: disable=missing-docstring
# pylint: disable=protected-access
# pylint <= 1.3
# pylint: disable=too-many-public-methods
# pylint >= 1.4
# pylint: disable=too-few-public-methods
# pylint: disable=no-member

import mock
import unittest
from gateway_code import config


class TestDefaultProfile(unittest.TestCase):

    @staticmethod
    @mock.patch('gateway_code.board_config.BoardConfig._find_board_type')
    def test_default_profile(mock_board_type):
        mock_board_type.return_value = 'm3'
        config.default_profile()
