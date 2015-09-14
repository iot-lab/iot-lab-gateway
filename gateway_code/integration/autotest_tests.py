# -*- coding: utf-8 -*-

""" Integration tests running autotests """

# pylint: disable=too-many-public-methods

import os
import sys
import mock

from nose.plugins.attrib import attr

from gateway_code.integration import test_integration_mock
from gateway_code.autotest import autotest
from gateway_code.utils.node_connection import OpenNodeConnection


@attr('autotest', 'integration')
class TestAutoTests(test_integration_mock.GatewayCodeMock):

    """ Try running autotests on node """

    def test_complete_auto_tests(self):
        """ Test a regular autotest """
        g_m = self.g_m
        # replace stop
        g_m.open_power_stop = mock.Mock(side_effect=g_m.open_power_stop)

        # call using rest
        self.request.query = mock.Mock(channel='22', gps='', flash='1')
        ret_dict = self.app.auto_tests(mode='blink')
        print >> sys.stderr, ret_dict
        self.assertEquals([], ret_dict['error'])
        self.assertIn('on_serial_echo', ret_dict['success'])
        self.assertTrue('GWT' in ret_dict['mac'])
        self.assertEquals(0, ret_dict['ret'])

        # test that ON still on
        if self.board_cfg.board_type == 'a8':
            # Don't know ip address, just check TTY
            self.assertTrue(os.path.exists(self.board_cfg.board_class.TTY))
        else:
            g_m.open_node.serial_redirection.start()
            ret = OpenNodeConnection.send_one_command(['get_time'])
            g_m.open_node.serial_redirection.stop()
            self.assertIsNotNone(ret)

    def test_mode_no_blink_no_radio(self):
        """ Try running autotest without blinking leds and without radio """

        g_v = autotest.AutoTestManager(self.g_m)
        ret_dict = g_v.auto_tests(channel=None, blink=False)

        self.assertEquals([], ret_dict['error'])
        self.assertEquals(0, ret_dict['ret'])
        # Radio functions not in results
        self.assertNotIn('test_radio_ping_pong', ret_dict['success'])
        self.assertNotIn('rssi_measures', ret_dict['success'])
