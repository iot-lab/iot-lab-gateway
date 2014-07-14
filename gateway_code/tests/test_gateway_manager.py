#! /usr/bin/env python

"""
Unit tests for gateway-manager
Complement the 'integration' tests
"""

import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = CURRENT_DIR + '/static/'  # 'static' symbolic link

import unittest
import mock
import os
from mock import patch

from gateway_code import gateway_manager


@patch('gateway_code.config.board_type', (lambda: 'M3'))
@patch('gateway_code.config.STATIC_FILES_PATH', STATIC_DIR)
class TestA8StartStop(unittest.TestCase):

    def test_setup(self):
        """ Test running gateway_manager with setup without error """

        g_m = gateway_manager.GatewayManager()
        g_m.node_flash = mock.Mock(return_value=0)
        try:
            g_m.setup()
        except StandardError:
            self.fail("Should not raise an exception during setup")

    def test_setup_fail_flash(self):
        """ Run setup with a flash fail error """
        g_m = gateway_manager.GatewayManager()
        g_m.node_flash = mock.Mock(return_value=1)
        self.assertRaises(StandardError, g_m.setup)

    def test_start_stop_a8_tty(self):
        """ Test running wait_tty_a8 and _wait_no_tty_a8 fcs """
        g_m = gateway_manager.GatewayManager()

        self.assertEquals(0, g_m.wait_tty_a8('/dev/null'))
        self.assertNotEquals(0, g_m.wait_tty_a8('no_tty_file'))

        self.assertNotEquals(0, g_m._wait_no_tty_a8('/dev/null'))
        self.assertEquals(0, g_m._wait_no_tty_a8('no_tty_file'))

    def test_create_and_cleanup_user_exp_files(self):
        """ Create files and clean them"""
        with patch('gateway_code.gateway_manager.config.EXP_FILES_DIR',
                   './iotlab/'):
            g_m = gateway_manager.GatewayManager()
            g_m._create_user_exp_folders('user', 123)
            g_m._create_user_exp_folders('user', 123)
            g_m._create_user_exp_files('user', 123)
            g_m._cleanup_user_exp_files()
            g_m._destroy_user_exp_folders('user', 123)
            g_m._destroy_user_exp_folders('user', 123)

    def test__create_user_exp_files_fail(self):
        """ Create user_exp files fail """
        g_m = gateway_manager.GatewayManager()
        self.assertRaises(IOError, g_m._create_user_exp_files,
                          'invalid_user_name', '-1')

    def test__cleanup_user_exp_files_fail_cases(self):
        """ Trying cleaning up files in different state """

        g_m = gateway_manager.GatewayManager()
        g_m.exp_desc['exp_files']['non_existent'] = "invalid_path_lala"
        g_m.exp_desc['exp_files']['empty_file'] = "test_file"
        g_m.exp_desc['exp_files']['non_empty_file'] = "test_file_2"
        open("test_file", 'w').close()
        with open('test_file_2', 'w') as test_file:
            test_file.write('test\n')

        g_m._cleanup_user_exp_files()

        # no exception
        self.assertFalse(os.path.exists("test_file"))
        self.assertTrue(os.path.exists("test_file_2"))
        os.unlink("test_file_2")