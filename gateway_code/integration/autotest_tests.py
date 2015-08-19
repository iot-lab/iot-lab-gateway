# -*- coding: utf-8 -*-

""" Integration tests running autotests """

# pylint: disable=too-many-public-methods

from sys import stderr
import mock

from nose.plugins.attrib import attr

from gateway_code.integration import test_integration_mock
from gateway_code.autotest import autotest, m3_node_interface

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
        self.assertIn('on_serial_echo', ret_dict['success'])
        self.assertTrue('GWT' in ret_dict['mac'])
        self.assertEquals(0, ret_dict['ret'])

        # test that ON still on => should be blinking and answering
        # TODO add fox
        if self.board_cfg.board_type != 'm3':
            return
        node = self.board_cfg.board_class
        open_serial = m3_node_interface.OpenNodeSerial(node.TTY, node.BAUDRATE)
        open_serial.start()
        self.assertIsNotNone(open_serial.send_command(['get_time']))
        open_serial.stop()

    def test_mode_no_blink_no_radio(self):
        """ Try running autotest without blinking leds and without radio """

        g_v = autotest.AutoTestManager(self.g_m)
        ret_dict = g_v.auto_tests(channel=None, blink=False)

        self.assertEquals([], ret_dict['error'])
        self.assertEquals(0, ret_dict['ret'])
        # Radio functions not in results
        self.assertNotIn('test_radio_ping_pong', ret_dict['success'])
        self.assertNotIn('rssi_measures', ret_dict['success'])
