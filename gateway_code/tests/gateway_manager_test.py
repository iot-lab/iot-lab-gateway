#! /usr/bin/env python

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


"""
Unit tests for gateway-manager
Complement the 'integration' tests
"""

import os

import unittest
import mock

from gateway_code import gateway_manager
from . import utils

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint >= 1.4
# pylint: disable=too-few-public-methods
# pylint: disable=no-member


@mock.patch(utils.READ_CONFIG, utils.read_config_mock('m3'))
class TestGatewayManager(unittest.TestCase):

    def test_setup(self):
        """ Test running gateway_manager with setup without error """
        g_m = gateway_manager.GatewayManager()
        g_m.control_node.setup = mock.Mock(return_value=0)
        try:
            g_m.setup()
        except StandardError:
            self.fail("Should not raise an exception during setup")

    def test_setup_fail_flash(self):
        """ Run setup with a flash fail error """
        g_m = gateway_manager.GatewayManager()
        g_m.control_node.setup = mock.Mock(return_value=1)
        self.assertRaises(StandardError, g_m.setup)

    def test_exp_update_profile_error(self):
        """ Update profile with an invalid profile """

        g_m = gateway_manager.GatewayManager()
        self.assertEquals(1, g_m.exp_update_profile(profile_dict={}))

# # # # # # # # # # # # # # # # # # # # #
# Measures folder and files management  #
# # # # # # # # # # # # # # # # # # # # #

    @mock.patch('gateway_code.config.EXP_FILES_DIR', './iotlab/')
    def test_create_and_del_user_exp_files(self):  # pylint:disable=no-self-use
        """ Create files and clean them"""
        g_m = gateway_manager.GatewayManager()
        g_m._create_user_exp_folders('user', 123)
        g_m._create_user_exp_folders('user', 123)
        exp_files = g_m.create_user_exp_files('m3-1', 'user', 123)
        g_m.cleanup_user_exp_files(exp_files)
        g_m._destroy_user_exp_folders('user', 123)
        g_m._destroy_user_exp_folders('user', 123)

    @mock.patch('gateway_code.config.EXP_FILES_DIR', './iotlab/')
    def test__create_user_exp_files_fail(self):
        """ Create user_exp files fail """
        g_m = gateway_manager.GatewayManager()
        self.assertRaises(IOError, g_m.create_user_exp_files,
                          'm3-1', '_user_', '-1')

    def test__cleanup_user_exp_files_fail_cases(self):
        """ Trying cleaning up files in different state """

        g_m = gateway_manager.GatewayManager()
        exp_files = {
            'non_existent': "invalid_path_lala",
            'empty_file': "test_file",
            'non_empty_file': "test_file_2",
        }

        open("test_file", 'w').close()
        with open('test_file_2', 'w') as test_file:
            test_file.write('test\n')

        g_m.cleanup_user_exp_files(exp_files)

        # no exception
        self.assertFalse(os.path.exists("test_file"))
        self.assertTrue(os.path.exists("test_file_2"))
        os.unlink("test_file_2")
