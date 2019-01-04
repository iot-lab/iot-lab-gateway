#! /usr/bin/env python
# -*- coding:utf-8 -*-

# This file is a part of IoT-LAB gateway_code
# Copyright (C) 2015 INRIA (Contact: admin@iot-lab.info)
# Contributor(s) : see AUTHORS file
#
# This software is governed by the CeCILL license under French law
# and abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# http://www.cecill.info.
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.


# pylint: disable=missing-docstring
# pylint: disable=protected-access
# pylint <= 1.3
# pylint: disable=too-many-public-methods
# pylint >= 1.4
# pylint: disable=too-few-public-methods
# pylint: disable=no-member

import unittest

import mock

import gateway_code.board_config as board_config
from . import utils


class TestBoardConfig(unittest.TestCase):

    @mock.patch(utils.CFG_VAR_PATH, utils.test_cfg_dir('m3_robot'))
    def test_board_type(self):
        board_cfg = board_config.BoardConfig()

        self.assertEqual('m3', board_cfg.board_type)
        self.assertEqual('m3', board_cfg.board_class.TYPE)
        self.assertEqual('turtlebot2', board_cfg.robot_type)
        self.assertNotEqual('', board_config.BoardConfig().node_id)

    @mock.patch(utils.CFG_VAR_PATH, utils.test_cfg_dir('m3_no_robot'))
    def test_board_type_no_robot(self):
        board_cfg = board_config.BoardConfig()

        self.assertEqual('m3', board_cfg.board_type)
        self.assertEqual(None, board_cfg.robot_type)

    @mock.patch(utils.CFG_VAR_PATH, utils.test_cfg_dir('invalid_board_type'))
    def test_board_type_not_found(self):
        self.assertRaises(ValueError, board_config.BoardConfig)
