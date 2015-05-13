#! /usr/bin/env python

"""
Unit tests for server-rest
Complement the 'integration' tests
"""

# pylint: disable=missing-docstring
# too long tests names
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint <= 1.3
# pylint: disable=too-many-public-methods
# pylint >= 1.4
# pylint: disable=too-few-public-methods
# pylint: disable=no-member

from cStringIO import StringIO

import mock
from mock import patch, PropertyMock
import unittest

from gateway_code import server_rest

import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


# Bottle FileUpload class stub
class FileUpload(object):  # pylint: disable=too-few-public-methods
    """ Bottle FileUpload class stub """
    files = {}

    def __init__(self, file_content, file_name):
        self.file = None
        self.filename = None
        self.name = None
        self.headers = None

        self.filename = file_name
        _ext = os.path.splitext(self.filename)[1]

        try:
            self.name = {'.json': 'profile', '.elf': 'firmware'}[_ext]
        except KeyError:
            raise ValueError("Uknown file type %r: %r" % (_ext, file_name))

        self.file = StringIO(file_content)


class TestRestMethods(unittest.TestCase):

    def setUp(self):
        self.request_patcher = patch('gateway_code.server_rest.request')
        self.request = self.request_patcher.start()

        self.board_patcher = patch('gateway_code.config.board_type')
        self.board = self.board_patcher.start()
        self.board.return_value = 'm3'

        self.g_m = mock.Mock()
        self.s_r = server_rest.GatewayRest(self.g_m)

    def tearDown(self):
        self.request_patcher.stop()
        self.board_patcher.stop()

    def test_exp_start_file_and_profile(self):
        idle = FileUpload('elf32arm0X1234', 'idle.elf')

        profile_str = '{ "profilename": "_default_profile", "power": "dc" }'
        profile_dict = {u'profilename': u'_default_profile', u'power': u'dc'}

        profile = FileUpload(profile_str, 'default_profile.json')
        self.g_m.exp_start.return_value = 0

        self.request.files = {'firmware': idle, 'profile': profile}
        ret_dict = self.s_r.exp_start('user', 123)
        self.assertEquals(0, ret_dict['ret'])

        # validate arguments
        call_args = self.g_m.exp_start.call_args[0]
        self.assertEquals(('user', 123), call_args[0: 2])
        self.assertTrue(idle.filename in call_args[2])
        self.assertEquals(profile_dict, call_args[3])

    def test_exp_start_invalid_profile(self):

        profile = FileUpload('invalid json profile}', 'inval_profile.json')

        self.request.files = {'profile': profile}
        ret_dict = self.s_r.exp_start('user', 123)
        self.assertNotEquals(0, ret_dict['ret'])

    def test_exp_start_no_files(self):
        self.g_m.exp_start.return_value = 0

        # nothing in files
        self.request.files = {}
        self.request.query = mock.Mock(timeout='')
        ret_dict = self.s_r.exp_start('user', 123)

        # validate
        self.g_m.exp_start.assert_called_with('user', 123, None, None, 0)
        self.assertEquals(0, ret_dict['ret'])

    def test_exp_start_valid_duration(self):
        self.g_m.exp_start.return_value = 0
        self.request.files = {}

        self.request.query = mock.Mock(timeout='12')
        self.s_r.exp_start('user', 123)
        self.g_m.exp_start.assert_called_with('user', 123, None, None, 12)

        # invalid data
        self.request.query = mock.Mock(timeout='ten_minutes')
        self.s_r.exp_start('user', 123)
        self.g_m.exp_start.assert_called_with('user', 123, None, None, 0)

        self.request.query = mock.Mock(timeout='-1')
        self.s_r.exp_start('user', 123)
        self.g_m.exp_start.assert_called_with('user', 123, None, None, 0)

    def test_exp_start_multipart_without_files(self):
        self.g_m.exp_start.return_value = 0

        self.request.files = mock.Mock()
        self.request.files.__contains__ = mock.Mock(side_effect=ValueError())
        self.request.files.__getitem__ = mock.Mock(side_effect=ValueError())
        self.request.query = mock.Mock(timeout='')
        ret_dict = self.s_r.exp_start('user', 123)

        # validate
        self.g_m.exp_start.assert_called_with('user', 123, None, None, 0)
        self.assertEquals(0, ret_dict['ret'])

    def test_exp_stop(self):
        self.g_m.exp_stop.return_value = 0
        ret_dict = self.s_r.exp_stop()
        self.assertEquals(0, ret_dict['ret'])

        self.g_m.exp_stop.return_value = 1
        ret_dict = self.s_r.exp_stop()
        self.assertEquals(1, ret_dict['ret'])

# Simple functions

    def test_exp_update_profile(self):
        self.g_m.exp_update_profile = mock.Mock(return_value=0)

        # No profile
        self.request.files = {}
        self.assertEquals({'ret': 0}, self.s_r.exp_update_profile())
        self.assertTrue(self.g_m.exp_update_profile.called)
        self.g_m.exp_update_profile.reset_mock()

        # default profile
        profile_str = '{ "profilename": "_default_profile", "power": "dc" }'
        self.request.files = {
            'profile': FileUpload(profile_str, 'default_profile.json')
        }
        self.assertEquals({'ret': 0}, self.s_r.exp_update_profile())
        self.assertTrue(self.g_m.exp_update_profile.called)
        self.g_m.exp_update_profile.reset_mock()

        # profile that cannot be decoded, invalid JSON
        # http://mock.readthedocs.org/en/latest/examples.html \
        #    #raising-exceptions-on-attribute-access
        type(self.request).json = PropertyMock(side_effect=ValueError)

        self.assertEquals({'ret': 1}, self.s_r.exp_update_profile())
        self.assertFalse(self.g_m.exp_update_profile.called)
        self.g_m.exp_update_profile.reset_mock()

    def test_set_time(self):
        self.g_m.set_time.return_value = 0
        ret_dict = self.s_r.set_time()
        self.assertEquals(0, ret_dict['ret'])

    def test_flash_function(self):
        idle = FileUpload('elf32arm0X1234', 'idle.elf')

        self.g_m.node_flash.return_value = 0

        self.request.files = {}
        ret_dict = self.s_r._flash('m3')
        self.assertNotEquals(0, ret_dict['ret'])

        # valid command
        self.request.files = {'firmware': idle}
        ret_dict = self.s_r._flash('gwt')
        self.assertEquals(0, ret_dict['ret'])

        call_args = self.g_m.node_flash.call_args[0]
        self.assertEquals('gwt', call_args[0])
        self.assertTrue(idle.filename in call_args[1])

    def test_generic_flash_wrappers(self):
        self.s_r._flash = mock.Mock(return_value={'ret': 0})

        ret_dict = self.s_r.open_flash()
        self.assertEquals(0, ret_dict['ret'])
        ret_dict = self.s_r.admin_control_flash()
        self.assertEquals(0, ret_dict['ret'])

    def test_reset_wrappers(self):
        self.g_m.node_soft_reset.return_value = 0

        ret_dict = self.s_r.open_soft_reset()
        self.assertEquals(0, ret_dict['ret'])
        ret_dict = self.s_r.admin_control_soft_reset()
        self.assertEquals(0, ret_dict['ret'])

    def test_open_start(self):
        self.g_m.open_power_start.return_value = 0

        ret_dict = self.s_r.open_start()
        self.assertEquals(0, ret_dict['ret'])

    def test_open_stop(self):
        self.g_m.open_power_stop.return_value = 0

        ret_dict = self.s_r.open_stop()
        self.assertEquals(0, ret_dict['ret'])

    def test_status(self):
        self.g_m.status.return_value = 0

        ret_dict = self.s_r.status()
        self.assertEquals(0, ret_dict['ret'])

    def auto_tests(self):
        self.g_m.auto_tests.return_value = {
            'ret': 0, 'error': [], 'success': ['test_ok'],
            'mac': {'A8': '12: 34: 56: 78: 9A: BC'}
        }

        self.request.query = mock.Mock(channel='', flash='', gps='')
        ret_dict = self.s_r.auto_tests(mode=None)
        self.assertEquals(0, ret_dict['ret'])
        self.g_m.auto_tests.assert_called_with(None, False, False, False)

        self.request.query = mock.Mock(channel='22', flash='1', gps='')
        ret_dict = self.s_r.auto_tests(mode='blink')
        self.assertEquals(0, ret_dict['ret'])
        self.g_m.auto_tests.assert_called_with(22, True, True, False)
        self.assertEquals(0, ret_dict['ret'])

        # invalid calls
        ret_dict = self.s_r.auto_tests(mode='nothing_valid')
        self.assertNotEquals(0, ret_dict['ret'])

        self.request.query = mock.Mock(channel='abc')
        ret_dict = self.s_r.auto_tests()
        self.assertNotEquals(0, ret_dict['ret'])
        self.request.query = mock.Mock(channel='42')
        ret_dict = self.s_r.auto_tests()
        self.assertNotEquals(0, ret_dict['ret'])

        self.request.query = mock.Mock(channel='11', gps='true')
        ret_dict = self.s_r.auto_tests()
        self.assertNotEquals(0, ret_dict['ret'])
        self.request.query = mock.Mock(channel='11', gps=None, flash='false')
        ret_dict = self.s_r.auto_tests()
        self.assertNotEquals(0, ret_dict['ret'])


# Patch to find '/var/log/config/board_type' -> tests/config_m3/board_type
@patch('gateway_code.config.GATEWAY_CONFIG_PATH', CURRENT_DIR + '/config_m3/')
class TestServerRestMain(unittest.TestCase):
    """ Cover functions uncovered by unit tests """

    @patch('subprocess.call')
    @patch('bottle.run')
    def test_main_function(self, run_mock, call_mock):
        call_mock.return_value = 0

        args = ['server_rest.py', 'localhost', '8080']
        server_rest._main(args)
        self.assertTrue(run_mock.called)
