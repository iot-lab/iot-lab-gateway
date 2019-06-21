# -*- coding:utf-8 -*-

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


# pylint: disable=missing-docstring
# pylint: disable=protected-access
# pylint: disable=too-many-public-methods
# pylint: disable=invalid-name

import unittest
import mock

from gateway_code import profile
from .. import cn_protocol


class TestProtocol(unittest.TestCase):

    def setUp(self):
        self.protocol = cn_protocol.Protocol(self._sender_wrapper)
        self.sender = mock.Mock()

    def _sender_wrapper(self, command_list):
        return self.sender(command_list)

    def test_consumption_start(self):

        self.sender.return_value = ['config_consumption_measure', 'ACK']

        # with full consumption
        consumption = profile.Consumption(alim='3.3V',
                                          source='dc',
                                          period=140,
                                          average=1,
                                          power=True,
                                          voltage=True,
                                          current=True)
        ret = self.protocol.config_consumption(consumption)
        self.assertEqual(0, ret)
        self.sender.assert_called_with(['config_consumption_measure', 'start',
                                        '3.3V', 'p', '1', 'v', '1', 'c', '1',
                                        '-p', '140', '-a', '1'])

        # consumption without all elements
        consumption = profile.Consumption(alim='3.3V',
                                          source='battery',
                                          period=8244,
                                          average=1024,
                                          power=True)
        ret = self.protocol.config_consumption(consumption)
        self.assertEqual(0, ret)
        self.sender.assert_called_with(['config_consumption_measure', 'start',
                                        'BATT', 'p', '1', 'v', '0', 'c', '0',
                                        '-p', '8244', '-a', '1024'])

    def test_consumption_stop(self):

        self.sender.return_value = ['config_consumption_measure', 'ACK']
        # no consumption object
        ret = self.protocol.config_consumption()
        self.sender.assert_called_with(['config_consumption_measure', 'stop'])
        self.assertEqual(0, ret)
        # power, voltage, current == False
        consumption = profile.Consumption(alim='3.3V',
                                          source='dc',
                                          period=140,
                                          average=1)
        ret = self.protocol.config_consumption(consumption)
        self.sender.assert_called_with(['config_consumption_measure', 'stop'])
        self.assertEqual(0, ret)

    def test_start_stop(self):

        self.sender.return_value = ['start', 'ACK']

        ret = self.protocol.start_stop('start', 'dc')
        self.sender.assert_called_with(['start', 'dc'])
        self.assertEqual(0, ret)

        # return NACK
        self.sender.return_value = ['start', 'ACK']
        ret = self.protocol.start_stop('stop', 'dc')
        self.sender.assert_called_with(['stop', 'dc'])
        self.assertEqual(1, ret)

        # return command different type
        self.sender.return_value = ['stop', 'NACK']
        ret = self.protocol.start_stop('stop', 'battery')
        self.sender.assert_called_with(['stop', 'battery'])
        self.assertEqual(1, ret)

    def test_set_time(self):

        self.sender.return_value = ['set_time', 'ACK']
        ret = self.protocol.set_time()
        self.sender.assert_called_with(['set_time'])
        self.assertEqual(0, ret)

        self.sender.return_value = ['set_time', 'NACK']
        ret = self.protocol.set_time()
        self.sender.assert_called_with(['set_time'])
        self.assertEqual(1, ret)

    def test_set_node_id(self):
        self.sender.return_value = ['set_node_id', 'ACK']
        ret = self.protocol.set_node_id('m3-1')
        self.sender.assert_called_with(['set_node_id', 'm3', '1'])
        self.assertEqual(0, ret)

        self.sender.return_value = ['set_node_id', 'ACK']
        ret = self.protocol.set_node_id('a8-256')
        self.sender.assert_called_with(['set_node_id', 'a8', '256'])
        self.assertEqual(0, ret)

        self.sender.call_count = 0
        ret = self.protocol.set_node_id('leonardo-256')
        assert self.sender.call_count == 0
        assert ret == 0

    def test_led_control(self):

        self.sender.return_value = ['green_led_blink', 'ACK']
        ret = self.protocol.green_led_blink()
        self.sender.assert_called_with(['green_led_blink'])
        self.assertEqual(0, ret)

        self.sender.return_value = ['green_led_on', 'ACK']
        ret = self.protocol.green_led_on()
        self.sender.assert_called_with(['green_led_on'])
        self.assertEqual(0, ret)


class TestProtocolRadio(unittest.TestCase):

    def setUp(self):
        self.protocol = cn_protocol.Protocol(self._sender_wrapper)
        self.sender = mock.Mock()

    def _sender_wrapper(self, command_list):
        return self.sender(command_list)

    def test_config_radio_with_measure(self):
        """ Configure Radio with 'measure' mode """
        radio = profile.Radio("rssi", [17, 15, 11], 100, num_per_channel=10)

        self.protocol._config_radio_measure = mock.Mock()
        self.protocol._config_radio_measure.return_value = 0
        self.protocol._stop_radio = mock.Mock()
        self.protocol._stop_radio.return_value = 0

        ret = self.protocol.config_radio(radio)
        self.assertEqual(0, ret)
        self.assertEqual(0, self.protocol._stop_radio.call_count)
        self.assertEqual(1, self.protocol._config_radio_measure.call_count)

    def test_config_radio_with_sniffer(self):
        """ Configure Radio with 'measure' mode """
        radio = profile.Radio("sniffer", [17], 0)

        self.protocol._config_radio_sniffer = mock.Mock()
        self.protocol._config_radio_sniffer.return_value = 0
        self.protocol._stop_radio = mock.Mock()
        self.protocol._stop_radio.return_value = 0

        ret = self.protocol.config_radio(radio)
        self.assertEqual(0, ret)
        self.assertEqual(0, self.protocol._stop_radio.call_count)
        self.assertEqual(1, self.protocol._config_radio_sniffer.call_count)

    def test_config_radio_with_none(self):
        """ Configure radio with None Radio profile """

        self.protocol._config_radio_measure = mock.Mock()
        self.protocol._config_radio_measure.return_value = 0
        self.protocol._stop_radio = mock.Mock()
        self.protocol._stop_radio.return_value = 0

        self.protocol.config_radio(None)
        self.assertEqual(0, self.protocol._config_radio_measure.call_count)
        self.assertEqual(1, self.protocol._stop_radio.call_count)

    def test_config_radio_with_invalid_mode(self):
        """ Configure radio with an non supported radio mode """
        radio = profile.Radio("rssi", [11], 10, num_per_channel=10)
        radio.mode = "invalid_mode"

        self.assertRaises(NotImplementedError,
                          self.protocol.config_radio, radio)

    def test_config_radio_error_during_config(self):

        radio = profile.Radio("rssi", [11], 10, num_per_channel=10)

        self.protocol._config_radio_measure = mock.Mock()
        self.protocol._config_radio_measure.return_value = 0xFF
        self.protocol._stop_radio = mock.Mock()
        self.protocol._stop_radio.return_value = 0

        ret = self.protocol.config_radio(radio)

        self.assertEqual(0xFF, ret)
        self.assertEqual(0, self.protocol._stop_radio.call_count)
        self.assertEqual(1, self.protocol._config_radio_measure.call_count)

    def test_config_radio_measure(self):

        radio = profile.Radio("rssi", [17, 15, 11], 100, num_per_channel=10)

        self.sender.return_value = ['config_radio_measure', 'ACK']
        ret = self.protocol._config_radio_measure(radio)
        self.sender.assert_called_with(['config_radio_measure', '11,15,17',
                                        '100', '10'])
        self.assertEqual(0, ret)

    def test_config_radio_sniffer(self):
        radio = profile.Radio("sniffer", [17, 15, 11], 100)

        self.sender.return_value = ['config_radio_sniffer', 'ACK']
        ret = self.protocol._config_radio_sniffer(radio)
        self.sender.assert_called_with(['config_radio_sniffer', '11,15,17',
                                        '100'])
        self.assertEqual(0, ret)

    def test__stop_radio(self):

        self.sender.return_value = ['config_radio_stop', 'ACK']

        ret = self.protocol._stop_radio()

        self.sender.assert_called_with(['config_radio_stop'])
        self.assertEqual(0, ret)
