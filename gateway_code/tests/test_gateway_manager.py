#! /usr/bin/env python

"""
Unit tests for gateway-manager
Complement the 'integration' tests
"""

import os

import unittest
import mock
from textwrap import dedent
from mock import patch

from gateway_code import gateway_manager
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = CURRENT_DIR + '/static/'  # 'static' symbolic link

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint <= 1.3
# pylint: disable=too-many-public-methods
# pylint >= 1.4
# pylint: disable=too-few-public-methods
# pylint: disable=no-member


@patch('gateway_code.config.board_type', (lambda: 'NOT_A_BOARD'))
class TestGatewayManagerInvalidBoardType(unittest.TestCase):
    def test_invalid_board_type(self):
        """ Run setup with a wrong board type"""
        self.assertRaises(ValueError, gateway_manager.GatewayManager)


@patch('gateway_code.config.board_type', (lambda: 'm3'))
@patch('gateway_code.config.STATIC_FILES_PATH', STATIC_DIR)
class TestGatewayManager(unittest.TestCase):

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

    def test_exp_update_profile_error(self):
        """ Update profile with an invalid profile """

        g_m = gateway_manager.GatewayManager()
        self.assertEquals(1, g_m.exp_update_profile(profile={}))

    def test_status(self):
        """ Test 'status' method """
        g_m = gateway_manager.GatewayManager()

        g_m._ftdi_is_present = mock.Mock(return_value=True)
        self.assertEquals(0, g_m.status())

        # no CN
        g_m._ftdi_is_present = mock.Mock(
            side_effect=(lambda x: {'CN': False, 'ON': True}[x]))
        self.assertEquals(1, g_m.status())
        # no ON
        g_m._ftdi_is_present = mock.Mock(
            side_effect=(lambda x: {'CN': True, 'ON': False}[x]))
        self.assertEquals(1, g_m.status())

    @patch('subprocess.check_output')
    def test__ftdi_is_present(self, check_output_mock):
        """ Test the '_ftdi_is_present' method """
        g_m = gateway_manager.GatewayManager()

        check_output_mock.return_value = dedent('''\
            FTx232 devices lister by IoT-LAB
            Listing FT4232 devices...
            Found 1 device(s)
            Device 0:
                Manufacturer: IoT-LAB
                Description: ControlNode
                Serial:
            All done, success!
            ''')
        self.assertEquals(True, g_m._ftdi_is_present('CN'))

        check_output_mock.return_value = dedent('''\
            FTx232 devices lister by IoT-LAB
            Listing FT2232 devices...
            No FTDI device found
            All done, success!
            ''')
        self.assertEquals(False, g_m._ftdi_is_present('ON'))

# # # # # # # # # # # # # # # # # # # # #
# Measures folder and files management  #
# # # # # # # # # # # # # # # # # # # # #

    @patch('gateway_code.config.EXP_FILES_DIR', './iotlab/')
    def test_create_and_del_user_exp_files(self):  # pylint:disable=no-self-use
        """ Create files and clean them"""
        g_m = gateway_manager.GatewayManager()
        g_m._create_user_exp_folders('user', 123)
        g_m._create_user_exp_folders('user', 123)
        g_m.create_user_exp_files('user', 123)
        g_m.cleanup_user_exp_files()
        g_m._destroy_user_exp_folders('user', 123)
        g_m._destroy_user_exp_folders('user', 123)

    @patch('gateway_code.config.EXP_FILES_DIR', './iotlab/')
    def test__create_user_exp_files_fail(self):
        """ Create user_exp files fail """
        g_m = gateway_manager.GatewayManager()
        self.assertRaises(IOError, g_m.create_user_exp_files, '_user_', '-1')

    def test__cleanup_user_exp_files_fail_cases(self):
        """ Trying cleaning up files in different state """

        g_m = gateway_manager.GatewayManager()
        g_m.exp_desc['exp_files']['non_existent'] = "invalid_path_lala"
        g_m.exp_desc['exp_files']['empty_file'] = "test_file"
        g_m.exp_desc['exp_files']['non_empty_file'] = "test_file_2"
        open("test_file", 'w').close()
        with open('test_file_2', 'w') as test_file:
            test_file.write('test\n')

        g_m.cleanup_user_exp_files()

        # no exception
        self.assertFalse(os.path.exists("test_file"))
        self.assertTrue(os.path.exists("test_file_2"))
        os.unlink("test_file_2")
