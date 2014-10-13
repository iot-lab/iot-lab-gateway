#! /usr/bin/env python
# -*- coding:utf-8 -*-

# pylint: disable=missing-docstring
# pylint: disable=too-many-public-methods
# pylint: disable=protected-access

import mock
import unittest

from cStringIO import StringIO

import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = CURRENT_DIR + '/static/'  # 'static' symbolic link

from gateway_code import config


class TestGetHostname(unittest.TestCase):
    def test_get_hosname(self):
        self.assertNotEquals('', config.hostname())


class TestDefaultProfile(unittest.TestCase):

    @staticmethod
    @mock.patch('gateway_code.config.STATIC_FILES_PATH', STATIC_DIR)
    @mock.patch('gateway_code.config.board_type', lambda: 'm3')
    def test_default_profile():
        config.default_profile()


class TestsBoardAndRobotType(unittest.TestCase):

    def setUp(self):
        config._BOARD_CONFIG = {}
        self.string_io = StringIO()

        self.open_mock_patcher = mock.patch('gateway_code.config.open',
                                            create=True)

        self.open_mock = self.open_mock_patcher.start()
        self.open_mock.return_value = self.string_io

    def tearDown(self):
        self.open_mock_patcher.stop()

    def test_board_type(self):

        self.string_io.write('M3\n')
        self.string_io.seek(0)
        config.board_type()

        self.assertEquals('m3', config.board_type())

        self.open_mock.side_effect = Exception()
        self.assertEquals('m3', config.board_type())

    def test_board_type_not_found(self):
        self.open_mock.side_effect = IOError()
        self.assertRaises(IOError, config.board_type)

    def test_robot_type(self):

        self.string_io.write('roomba\n')
        self.string_io.seek(0)
        self.assertEquals('roomba', config.robot_type())

        self.open_mock.side_effect = Exception()
        self.assertEquals('roomba', config.robot_type())

    def test_robot_type_not_found(self):
        self.open_mock.side_effect = IOError()
        self.assertEquals(None, config.robot_type())
