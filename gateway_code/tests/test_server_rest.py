#! /usr/bin/env python

"""
Unit tests for server-rest
Complement the 'integration' tests
"""

from cStringIO import StringIO

import mock
from mock import patch
import unittest

import recordtype

import gateway_code
from gateway_code import server_rest

import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR  = CURRENT_DIR + '/static/' # using the 'static' symbolic link


# Bottle FileUpload class stub
FileUpload = recordtype.recordtype('FileUpload', \
        ['file', 'name', 'filename', ('headers', None)])



class TestRestMethods(unittest.TestCase):

    def setUp(self):
        self.request_patcher = patch('gateway_code.server_rest.request')
        self.request = self.request_patcher.start()

        self.board_patcher = patch('gateway_code.config.board_type')
        self.board = self.board_patcher.start()
        self.board.return_value = 'M3'

    def tearDown(self):
        self.request_patcher.stop()
        self.board_patcher.stop()


    def test_exp_start_with_file_and_profile(self):
        idle = FileUpload(file = StringIO('empty_firmware'),
                name = 'firmware', filename = 'idle.elf')

        profile_str = '{ "profilename": "_default_profile", "power": "dc" }'
        profile_dict = {u'profilename': u'_default_profile', u'power': u'dc'}

        default_profile = FileUpload(\
                file = StringIO(profile_str),
                name = 'profile', filename = 'default_profile.json')

        g_m = mock.Mock()
        s_r = server_rest.GatewayRest(g_m)
        g_m.exp_start.return_value = 0

        self.request.files = {'firmware': idle, 'profile': default_profile}
        ret_dict = s_r.exp_start('123', 'username')
        self.assertEquals(0, ret_dict['ret'])

        # validate arguments
        call_args = g_m.exp_start.call_args[0]
        self.assertEquals((123, 'username'), call_args[0:2])
        self.assertTrue(idle.filename in call_args[2])
        self.assertEquals(profile_dict, call_args[3])

    def test_exp_start_invalid_profile(self):

        profile = FileUpload(file=StringIO('not a valid profile json, }'),
            name='profile', filename='default_profile.json')

        s_r = server_rest.GatewayRest(None)

        self.request.files = {'profile': profile}
        ret_dict = s_r.exp_start('123', 'username')
        self.assertNotEquals(0, ret_dict['ret'])


    def test_exp_start_no_files(self):
        g_m = mock.Mock()
        s_r = server_rest.GatewayRest(g_m)
        g_m.exp_start.return_value = 0

        # nothing in files
        self.request.files = {}
        ret_dict = s_r.exp_start('123', 'username')

        # validate
        g_m.exp_start.assert_called_with(123, 'username', None, None)
        self.assertEquals(0, ret_dict['ret'])


    def test_exp_start_multipart_without_files(self):
        g_m = mock.Mock()
        s_r = server_rest.GatewayRest(g_m)
        g_m.exp_start.return_value = 0

        self.request.files = mock.Mock()
        self.request.files.__contains__ = mock.Mock(side_effect=ValueError())
        ret_dict = s_r.exp_start('123', 'username')

        # validate
        g_m.exp_start.assert_called_with(123, 'username', None, None)
        self.assertEquals(0, ret_dict['ret'])


    def test_exp_stop(self):
        g_m = mock.Mock()
        s_r = server_rest.GatewayRest(g_m)

        g_m.exp_stop.return_value = 0
        ret_dict = s_r.exp_stop()
        self.assertEquals(0, ret_dict['ret'])

        g_m.exp_stop.return_value = 1
        ret_dict = s_r.exp_stop()
        self.assertEquals(1, ret_dict['ret'])


    def test_reset_time(self):
        g_m = mock.Mock()
        s_r = server_rest.GatewayRest(g_m)

        g_m.reset_time.return_value = 0
        ret_dict = s_r.reset_time()
        self.assertEquals(0, ret_dict['ret'])


    def test_flash_function(self):
        idle = FileUpload(file = StringIO('empty_firmware'),
                name = 'firmware', filename = 'idle.elf')

        g_m = mock.Mock()
        s_r = server_rest.GatewayRest(g_m)
        g_m.node_flash.return_value = 0

        self.request.files = {}
        ret_dict = s_r._flash('m3')
        self.assertNotEquals(0, ret_dict['ret'])

        # valide command
        self.request.files = {'firmware': idle}
        ret_dict = s_r._flash('gwt')
        self.assertEquals(0, ret_dict['ret'])

        call_args = g_m.node_flash.call_args[0]
        self.assertEquals('gwt', call_args[0])
        self.assertTrue(idle.filename in call_args[1])



    def test_generic_flash_wrappers(self):
        g_m = mock.Mock()
        s_r = server_rest.GatewayRest(g_m)
        s_r._flash = mock.Mock(return_value={'ret': 0})

        ret_dict = s_r.open_flash()
        self.assertEquals(0, ret_dict['ret'])
        ret_dict = s_r.admin_control_flash()
        self.assertEquals(0, ret_dict['ret'])

    def test_reset_wrappers(self):
        g_m = mock.Mock()
        s_r = server_rest.GatewayRest(g_m)
        g_m.node_soft_reset.return_value = 0

        ret_dict = s_r.open_soft_reset()
        self.assertEquals(0, ret_dict['ret'])
        ret_dict = s_r.admin_control_soft_reset()
        self.assertEquals(0, ret_dict['ret'])

    def test_open_start(self):
        g_m = mock.Mock()
        s_r = server_rest.GatewayRest(g_m)
        g_m.open_power_start.return_value = 0

        ret_dict = s_r.open_start()
        self.assertEquals(0, ret_dict['ret'])

    def test_open_stop(self):
        g_m = mock.Mock()
        s_r = server_rest.GatewayRest(g_m)
        g_m.open_power_stop.return_value = 0

        ret_dict = s_r.open_stop()
        self.assertEquals(0, ret_dict['ret'])

    def auto_tests(self):
        g_m = mock.Mock()
        s_r = server_rest.GatewayRest(g_m)
        g_m.auto_tests.return_value = (0, [], ['test_ok'])

        self.request.query = mock.Mock(channel='')
        ret_dict = s_r.auto_tests(mode=None)
        self.assertEquals(0, ret_dict['ret'])
        g_m.auto_tests.assert_called_with(None, False)

        self.request.query = mock.Mock(channel='22')
        ret_dict = s_r.auto_tests(mode='blink')
        self.assertEquals(0, ret_dict['ret'])
        g_m.auto_tests.assert_called_with(22, True)
        self.assertEquals(0, ret_dict['ret'])

        # invalid calls
        ret_dict = s_r.auto_tests(mode='nothing_valid')
        self.assertNotEquals(0, ret_dict['ret'])

        self.request.query = mock.Mock(channel='abc')
        ret_dict = s_r.auto_tests()
        self.assertNotEquals(0, ret_dict['ret'])
        self.request.query = mock.Mock(channel='42')
        ret_dict = s_r.auto_tests()
        self.assertNotEquals(0, ret_dict['ret'])


# Patch to find idle.elf
# Patch to find control_node.elf at start
# Patch to find '/var/log/config/board_type' -> tests/config_m3/board_type
MOCK_FIRMWARES = {
    'idle': STATIC_DIR + 'idle.elf',
    'control_node': STATIC_DIR + 'control_node.elf',
    }
@patch('gateway_code.openocd_cmd.config.STATIC_FILES_PATH', new=STATIC_DIR)
@patch('gateway_code.gateway_manager.config.FIRMWARES', MOCK_FIRMWARES)
@patch('gateway_code.config.GATEWAY_CONFIG_PATH', CURRENT_DIR + '/config_m3/')
class TestServerRestMain(unittest.TestCase):
    """
    Cover functions uncovered by unit tests
    """

    @patch('subprocess.Popen')
    @patch('bottle.run')
    def test_main_function(self, run_mock, mock_popen):
        popen = mock_popen.return_value
        popen.communicate.return_value = (mock_out, mock_err) = ("OUT_MSG", "")
        popen.returncode = mock_ret = 0

        args = ['server_rest.py', 'localhost', '8080']
        gateway_code.server_rest._main(args)

