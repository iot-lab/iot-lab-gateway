#! /usr/bin/env python
# -*- coding:utf-8 -*-

# pylint: disable=missing-docstring
# pylint: disable=protected-access
# pylint >= 1.4
# pylint: disable=too-few-public-methods
# pylint: disable=no-member

import os
import mock
import unittest

from gateway_code.open_nodes.node_m3 import NodeM3
from gateway_code.open_nodes.node_a8 import NodeA8

from gateway_code import config
from . import utils


class TestConfig(unittest.TestCase):

    def test_open_node_class(self):
        self.assertEquals(NodeM3, config.open_node_class('m3'))
        self.assertEquals(NodeA8, config.open_node_class('a8'))

    def test_open_node_class_errors(self):
        # No module
        self.assertRaisesRegexp(
            ValueError, '^Board unknown not implemented: ImportError.*$',
            config.open_node_class, 'unknown')

        # No Class in module
        with mock.patch('gateway_code.config.OPEN_CLASS_NAME', 'UnknownClass'):
            self.assertRaisesRegexp(
                ValueError, '^Board m3 not implemented: AttributeError.*$',
                config.open_node_class, 'm3')

    def test_read_config(self):
        with mock.patch(utils.CFG_VAR_PATH, utils.test_cfg_dir('m3_no_robot')):
            self.assertEquals('m3', config.read_config('board_type'))
            self.assertEquals('m3', config.read_config('board_type', 'def'))

            self.assertRaises(IOError, config.read_config, 'robot')
            self.assertEquals(None, config.read_config('robot', None))

        with mock.patch(utils.CFG_VAR_PATH, utils.test_cfg_dir('m3_robot')):
            self.assertEquals('m3', config.read_config('board_type'))
            self.assertEquals('turtlebot2', config.read_config('robot'))

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
