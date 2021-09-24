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
from __future__ import print_function

import os
import sys

from gateway_code.autotest.autotest import AutoTestManager
from gateway_code.integration import test_integration_mock
from gateway_code.utils.node_connection import OpenNodeConnection
from gateway_code.tests.rest_server_test import query_string


class TestAutoTests(test_integration_mock.GatewayCodeMock):
    """ Try running autotests on node """

    def test_complete_auto_tests(self):
        """ Test a regular autotest """
        # call with channel/flash/no_gps and blinking leds
        extra = query_string('channel=22&flash=1&gps=')
        ret = self.server.put('/autotest/blink', extra_environ=extra)
        ret_dict = ret.json
        ret_string = '{}\n'.format(ret_dict)
        sys.stderr.write(ret_string)

        self.assertEqual([], ret_dict['error'])
        self.assertIn('on_serial_echo', ret_dict['success'])
        self.assertTrue('GWT' in ret_dict['mac'])
        self.assertEqual(0, ret_dict['ret'])

        # test that ON still on
        if self.board_cfg.board_type in ('a8', 'rpi3'):
            # Don't know ip address, just check TTY
            self.assertTrue(os.path.exists(self.board_cfg.board_class.TTY))
        else:
            self.g_m.open_node.serial_redirection.start()
            ret = OpenNodeConnection.send_one_command(['get_time'])
            self.g_m.open_node.serial_redirection.stop()
            self.assertIsNotNone(ret)

        if self.board_cfg.linux_on_class is not None:
            autotest = self.board_cfg.linux_on_class.AUTOTEST_AVAILABLE
            not_tested = (set(autotest) -
                          set(AutoTestManager.TESTED_FEATURES))
        else:
            not_tested = (set(self.g_m.open_node.AUTOTEST_AVAILABLE) -
                          set(AutoTestManager.TESTED_FEATURES))

        self.assertEqual(not_tested, set())

    def test_mode_no_blink_no_radio(self):
        """ Try running autotest without blinking leds and without radio """
        ret = self.server.put('/autotest')
        ret_dict = ret.json

        self.assertEqual([], ret_dict['error'])
        self.assertEqual(0, ret_dict['ret'])
        # Radio functions not in results
        self.assertNotIn('test_radio_ping_pong', ret_dict['success'])
        self.assertNotIn('rssi_measures', ret_dict['success'])
