#! /usr/bin/env python
#-*- coding:utf-8 -*-


import mock
import unittest

from cStringIO import StringIO

from gateway_code import config

class TestsBoardAndRobotType(unittest.TestCase):

    def setUp(self):
        config._BOARD_CONFIG = {}
        self.string_io = StringIO()

        self.open_mock_patcher = mock.patch('gateway_code.config.open', create=True)

        self.open_mock = self.open_mock_patcher.start()
        self.open_mock.return_value = mock.Mock()
        self.open_mock.return_value.__enter__ = mock.Mock(return_value=self.string_io)
        self.open_mock.return_value.__exit__ = mock.Mock(return_value=None)

    def tearDown(self):
        self.open_mock_patcher.stop()


    def test_board_type(self):

        self.string_io.write('M3\n')
        self.string_io.seek(0)
        ret = config.board_type()

        self.assertEquals('M3', config.board_type())

        self.open_mock.side_effect = Exception()
        self.assertEquals('M3', config.board_type())


    def test_board_type_not_found(self):
        self.open_mock.side_effect = IOError()
        self.assertRaises(StandardError, config.board_type)



    def test_robot_type(self):

        self.string_io.write('roomba\n')
        self.string_io.seek(0)
        self.assertEquals('roomba', config.robot_type())

        self.open_mock.side_effect = Exception()
        self.assertEquals('roomba', config.robot_type())

    def test_robot_type_not_found(self):
        self.open_mock.side_effect = IOError()
        self.assertEquals(None, config.robot_type())
