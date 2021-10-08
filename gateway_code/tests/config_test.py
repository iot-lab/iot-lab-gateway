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

import mock

from gateway_code import config
from . import utils


class TestConfig(unittest.TestCase):

    def test_read_config(self):
        with mock.patch(utils.CFG_VAR_PATH, utils.test_cfg_dir('m3_no_robot')):
            self.assertEqual('m3', config.read_config('board_type'))
            self.assertEqual('m3', config.read_config('board_type', 'def'))

            self.assertRaises(IOError, config.read_config, 'robot')
            self.assertEqual(None, config.read_config('robot', None))

        with mock.patch(utils.CFG_VAR_PATH, utils.test_cfg_dir('m3_robot')):
            self.assertEqual('m3', config.read_config('board_type'))
            self.assertEqual('turtlebot2', config.read_config('robot'))

    def test_default_profile(self):
        default_profile_dict = {
            'power': 'dc',
            'profilename': '_default_profile',
        }
        self.assertEqual(default_profile_dict, config.DEFAULT_PROFILE)

    @staticmethod
    def _rmfile(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass

    def test_user_files(self):
        file_path = f'/tmp/test_{os.uname()[1]}'
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
