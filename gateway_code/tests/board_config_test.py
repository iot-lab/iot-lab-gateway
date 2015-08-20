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
import gateway_code.board_config as board_config
from . import utils


class TestBoardConfig(unittest.TestCase):

    @mock.patch(utils.CFG_VAR_PATH, utils.test_cfg_dir('m3_robot'))
    def test_board_type(self):
        board_cfg = board_config.BoardConfig()

        self.assertEquals('m3', board_cfg.board_type)
        self.assertEquals('m3', board_cfg.board_class.TYPE)
        self.assertEquals('turtlebot2', board_cfg.robot_type)
        self.assertNotEquals('', board_config.BoardConfig().node_id)

    @mock.patch(utils.CFG_VAR_PATH, utils.test_cfg_dir('m3_no_robot'))
    def test_board_type_no_robot(self):
        board_cfg = board_config.BoardConfig()

        self.assertEquals('m3', board_cfg.board_type)
        self.assertEquals(None, board_cfg.robot_type)

    @mock.patch(utils.CFG_VAR_PATH, utils.test_cfg_dir('invalid_board_type'))
    def test_board_type_not_found(self):
        self.assertRaises(ValueError, board_config.BoardConfig)
