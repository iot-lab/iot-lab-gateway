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
Unit tests for server-rest
Complement the 'integration' tests
"""

# pylint: disable=missing-docstring
# too long tests names
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=too-few-public-methods
# pylint: disable=no-member

import unittest

import webtest
import mock

from gateway_code import rest_server
from . import utils


def query_string(query_str):
    """ Create extra_environ to add query_string to POST/PUT requests

    Query Strings should not be used for POST/PUT, but it's the case anyway
    so find way to make it work.

    :param query_str: query string
    :returns: an extra_environ dict for webtest """
    return {'QUERY_STRING': query_str}


class TestRestMethods(unittest.TestCase):

    EXP_START = '/exp/start/{exp_id}/{user}'.format(user='user', exp_id=123)

    PROFILE_STR = '{ "profilename": "_default_profile", "power": "dc" }'
    PROFILE_DICT = {u'profilename': u'_default_profile', u'power': u'dc'}

    def setUp(self):
        mock.patch(utils.READ_CONFIG, utils.read_config_mock('m3')).start()

        self.g_m = mock.Mock()
        self.s_r = rest_server.GatewayRest(self.g_m)
        self.server = webtest.TestApp(self.s_r)

    def tearDown(self):
        mock.patch.stopall()

    def test_routes(self):
        with mock.patch.object(self.s_r, 'route') as m_route:

            def _func():
                pass

            ret = self.s_r.conditional_route('flash', '/test', 'POST', _func)
            self.assertTrue(m_route.called)
            self.assertIsNotNone(ret)
            m_route.reset_mock()

            # Not a function
            ret = self.s_r.conditional_route('TTY', '/test', 'POST', _func)
            self.assertFalse(m_route.called)
            self.assertIsNone(ret)
            m_route.reset_mock()

            # Non existant
            ret = self.s_r.conditional_route('UNKNOWN', '/test', 'POST', _func)
            self.assertFalse(m_route.called)
            self.assertIsNone(ret)
            m_route.reset_mock()

    def test_exp_start_file_and_profile(self):
        self.g_m.exp_start.return_value = 0

        files = []
        files += [('firmware', 'idle.elf', 'elf32arm0X1234')]
        files += [('profile', 'profile.json', self.PROFILE_STR)]

        ret = self.server.post(self.EXP_START, upload_files=files)
        self.assertEquals(0, ret.json['ret'])

        # validate arguments
        call_args = self.g_m.exp_start.call_args[0]
        self.assertEquals(('user', 123), call_args[0: 2])
        self.assertTrue('idle.elf' in call_args[2])
        self.assertEquals(self.PROFILE_DICT, call_args[3])

    def test_exp_start_invalid_profile(self):

        files = [('profile', 'inval_profile.json', 'invalid json profile}')]
        ret = self.server.post(self.EXP_START, upload_files=files)
        self.assertEquals(1, ret.json['ret'])

    def test_exp_start_no_files(self):
        self.g_m.exp_start.return_value = 0

        # nothing in files
        ret = self.server.post(self.EXP_START, upload_files=[])
        self.assertEquals(0, ret.json['ret'])

        # validate
        self.g_m.exp_start.assert_called_with('user', 123, None, None, 0)
        self.assertEquals(0, ret.json['ret'])

    def test_exp_start_valid_duration(self):
        self.g_m.exp_start.return_value = 0

        extra = query_string('timeout=12')
        self.server.post(self.EXP_START, extra_environ=extra)
        self.g_m.exp_start.assert_called_with('user', 123, None, None, 12)

        # invalid data
        extra = query_string('timeout=ten_minutes')
        self.server.post(self.EXP_START, extra_environ=extra)
        self.g_m.exp_start.assert_called_with('user', 123, None, None, 0)

        extra = query_string('timeout=-1')
        self.server.post(self.EXP_START, extra_environ=extra)
        self.g_m.exp_start.assert_called_with('user', 123, None, None, 0)

    def test_exp_start_multipart_without_files(self):
        self.g_m.exp_start.return_value = 0

        ret = self.server.post(self.EXP_START,
                               content_type='multipart/form-data')

        self.assertEquals(0, ret.json['ret'])
        self.g_m.exp_start.assert_called_with('user', 123, None, None, 0)

    def test_exp_stop(self):
        self.g_m.exp_stop.return_value = 0
        ret = self.server.delete('/exp/stop')
        self.assertEquals(0, ret.json['ret'])

        self.g_m.exp_stop.return_value = 1
        ret = self.server.delete('/exp/stop')
        self.assertEquals(1, ret.json['ret'])

    def test_exp_stop_wrong_request_type(self):
        ret = self.server.post('/exp/stop', status='*')
        self.assertEquals(405, ret.status_int)
        self.assertEquals('405 Method Not Allowed', ret.status)

# Simple functions

    def test_exp_update_profile(self):
        app_json = 'application/json'

        self.g_m.exp_update_profile = mock.Mock(return_value=0)

        # No profile
        ret = self.server.post('/exp/update', content_type=app_json)
        self.assertEquals(0, ret.json['ret'])
        self.assertTrue(self.g_m.exp_update_profile.called)
        self.g_m.exp_update_profile.reset_mock()

        # default profile
        ret = self.server.post('/exp/update', self.PROFILE_STR,
                               content_type=app_json)
        self.assertEquals(0, ret.json['ret'])
        self.assertTrue(self.g_m.exp_update_profile.called)

        call_args = self.g_m.exp_update_profile.call_args[0]
        self.assertEquals(self.PROFILE_DICT, call_args[0])
        self.g_m.exp_update_profile.reset_mock()

        # profile that cannot be decoded, invalid JSON
        ret = self.server.post('/exp/update', 'inval }', content_type=app_json)
        self.assertEquals(1, ret.json['ret'])
        self.assertFalse(self.g_m.exp_update_profile.called)
        self.g_m.exp_update_profile.reset_mock()

    def test_flash_function(self):
        self.g_m.open_flash.return_value = 0
        files = [('firmware', 'idle.elf', 'elf32arm0X1234')]

        # valid command
        ret = self.server.post('/open/flash', upload_files=files)
        self.assertEquals(0, ret.json['ret'])

        # Error no firmware
        ret = self.server.post('/open/flash', upload_files=[])
        self.assertEquals(1, ret.json['ret'])

    def test_flash_idle(self):
        self.g_m.node_flash.return_value = 0

        ret = self.server.put('/open/flash/idle')
        self.assertEquals(0, ret.json['ret'])
        self.g_m.node_flash.assert_called_with('open', None)

    def test_reset_wrappers(self):
        self.g_m.open_reset.return_value = 0

        ret = self.server.put('/open/reset')
        self.assertEquals(0, ret.json['ret'])

    def test_open_start(self):
        self.g_m.open_power_start.return_value = 0

        ret = self.server.put('/open/start')
        self.assertEquals(0, ret.json['ret'])

    def test_open_stop(self):
        self.g_m.open_power_stop.return_value = 0

        ret = self.server.put('/open/stop')
        self.assertEquals(0, ret.json['ret'])

    def test_status(self):
        self.g_m.status.return_value = 0

        ret = self.server.get('/status')
        self.assertEquals(0, ret.json['ret'])

    def auto_tests(self):
        self.g_m.auto_tests.return_value = {
            'ret': 0, 'error': [], 'success': ['test_ok'],
            'mac': {'A8': '12: 34: 56: 78: 9A: BC'}
        }

        ret = self.server.put('/autotest')
        self.assertEquals(0, ret.json['ret'])
        self.g_m.auto_tests.assert_called_with(None, False, False, False)

        extra = query_string('channel=22&flash=1&gps=')
        ret = self.server.put('/autotest/blink', extra_environ=extra)
        self.assertEquals(0, ret.json['ret'])
        self.g_m.auto_tests.assert_called_with(22, True, True, False)

        # invalid calls
        ret = self.server.put('/autotest/invalid_mode')
        self.assertNotEquals(0, ret.json['ret'])

        extra = query_string('channel=abc')
        ret = self.server.put('/autotest', extra_environ=extra)
        self.assertEquals(1, ret.json['ret'])

        extra = query_string('channel=42')
        ret = self.server.put('/autotest', extra_environ=extra)
        self.assertEquals(1, ret.json['ret'])

        extra = query_string('channel=11&gps=true')
        ret = self.server.put('/autotest', extra_environ=extra)
        self.assertEquals(1, ret.json['ret'])

        extra = query_string('channel=11&flash=false')
        ret = self.server.put('/autotest', extra_environ=extra)
        self.assertEquals(1, ret.json['ret'])


class TestServerRestMain(unittest.TestCase):
    """ Cover functions uncovered by unit tests """

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('m3'))
    @mock.patch('gateway_code.utils.subprocess_timeout.call')  # CN flash
    @mock.patch('bottle.run')
    def test_main_function(self, run_mock, call_mock):
        call_mock.return_value = 0
        args = ['rest_server.py', 'localhost', '8080']
        rest_server._main(args)
        self.assertTrue(run_mock.called)
