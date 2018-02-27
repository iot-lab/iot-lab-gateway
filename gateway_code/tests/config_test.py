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
# pylint >= 1.4
# pylint: disable=too-few-public-methods
# pylint: disable=no-member

import os
import unittest

from gateway_code import config
from gateway_code.board_config import BoardConfig
from . import utils


class TestConfig(unittest.TestCase):

    def test_read_config(self):
        board_config = BoardConfig.from_file(utils.test_cfg_dir('m3_no_robot'))
        self.assertEquals('m3', board_config.board_type)
        self.assertEquals(None, board_config.robot_type)

        board_config = BoardConfig.from_file(utils.test_cfg_dir('m3_robot'))
        self.assertEquals('m3', board_config.board_type)
        self.assertEquals('turtlebot2', board_config.robot_type)

    def test_default_profile(self):
        default_profile_dict = {
            u'power': u'dc',
            u'profilename': u'_default_profile',
        }
        self.assertEquals(default_profile_dict, config.DEFAULT_PROFILE)

    @staticmethod
    def _rmfile(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass

    def test_user_files(self):
        file_path = '/tmp/test_%s' % os.uname()[1]
        self._rmfile(file_path)

        config.create_user_file(file_path)
        self.assertTrue(os.path.exists(file_path))
        config.clean_user_file(file_path)
        self.assertFalse(os.path.exists(file_path))

        config.create_user_file(file_path)
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, 'w+') as _file:
            _file.write('DATA\n')
        config.clean_user_file(file_path)
        self.assertTrue(os.path.exists(file_path))  # not empty, still here

        self._rmfile(file_path)
