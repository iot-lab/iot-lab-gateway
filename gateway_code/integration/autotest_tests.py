# -*- coding: utf-8 -*-

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


""" Integration tests running autotests """

# pylint: disable=too-many-public-methods

import os
import sys

from nose.plugins.attrib import attr

from gateway_code.autotest.autotest import AutoTestManager
from gateway_code.integration import test_integration_mock
from gateway_code.utils.node_connection import OpenNodeConnection
from gateway_code.tests.rest_server_test import query_string


@attr('autotest', 'integration')
class TestAutoTests(test_integration_mock.GatewayCodeMock):
    """ Try running autotests on node """

    def test_complete_auto_tests(self):
        """ Test a regular autotest """
        # call with channel/flash/no_gps and blinking leds
        extra = query_string('channel=22&flash=1&gps=')
        ret = self.server.put('/autotest/blink', extra_environ=extra)
        ret_dict = ret.json
        print >> sys.stderr, ret_dict

        self.assertEquals([], ret_dict['error'])
        self.assertIn('on_serial_echo', ret_dict['success'])
        self.assertTrue('GWT' in ret_dict['mac'])
        self.assertEquals(0, ret_dict['ret'])

        # test that ON still on
        if self.board_cfg.board_type == 'a8':
            # Don't know ip address, just check TTY
            self.assertTrue(os.path.exists('/dev/ttyON'))
        else:
            self.g_m.open_node.serial_redirection.start()
            ret = OpenNodeConnection.send_one_command(['get_time'])
            self.g_m.open_node.serial_redirection.stop()
            self.assertIsNotNone(ret)

        not_tested = (set(self.g_m.open_node.AUTOTEST_AVAILABLE) -
                      set(AutoTestManager.TESTED_FEATURES))
        self.assertEquals(not_tested, set())

    def test_mode_no_blink_no_radio(self):
        """ Try running autotest without blinking leds and without radio """
        ret = self.server.put('/autotest')
        ret_dict = ret.json

        self.assertEquals([], ret_dict['error'])
        self.assertEquals(0, ret_dict['ret'])
        # Radio functions not in results
        self.assertNotIn('test_radio_ping_pong', ret_dict['success'])
        self.assertNotIn('rssi_measures', ret_dict['success'])
