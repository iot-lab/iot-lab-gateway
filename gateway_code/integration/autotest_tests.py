# -*- coding: utf-8 -*-

""" Integration tests running autotests """

# pylint: disable=too-many-public-methods

from sys import stderr
import mock

from nose.plugins.attrib import attr

from gateway_code.integration import test_integration_mock

import gateway_code.autotest.m3_node_interface
import gateway_code.autotest.autotest
from gateway_code.open_nodes.node_m3 import NodeM3
import gateway_code.config

import gateway_code.board_config as board_config

import os
if os.uname()[4] != 'armv7l':
    import unittest
    raise unittest.SkipTest("Skip board embedded tests")


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
        print >> stderr, ret_dict
        self.assertEquals([], ret_dict['error'])
        self.assertTrue('GWT' in ret_dict['mac'])
        self.assertEquals(0, ret_dict['ret'])

        # test that ON still on => should be blinking and answering
        # TODO add fox
        if board_config.BoardConfig().board_type != 'm3':
            return
        open_serial = gateway_code.autotest.m3_node_interface.OpenNodeSerial(
            open_node.NodeM3.TTY, open_node.NodeM3.BAUDRATE)
        open_serial.start()
        self.assertIsNotNone(open_serial.send_command(['get_time']))
        open_serial.stop()

    def test_mode_no_blink_no_radio(self):
        """ Try running autotest without blinking leds and without radio """

        g_v = gateway_code.autotest.autotest.AutoTestManager(self.g_m)
        ret_dict = g_v.auto_tests(channel=None, blink=False)

        self.assertEquals([], ret_dict['error'])
        self.assertEquals(0, ret_dict['ret'])
        # Radio functions not in results
        self.assertNotIn('test_radio_ping_pong', ret_dict['success'])
        self.assertNotIn('rssi_measures', ret_dict['success'])
