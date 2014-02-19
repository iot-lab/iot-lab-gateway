# -*- coding:utf-8 -*-


import unittest
import mock

from gateway_code import protocol_cn
from gateway_code import profile



class TestProtocol(unittest.TestCase):


    def setUp(self):
        self.protocol = protocol_cn.Protocol(self._sender_wrapper)
        self.sender = mock.Mock()



    def _sender_wrapper(self, command_list):
        return self.sender(command_list)



    def test_consumption_start(self):

        self.sender.return_value = ['config_consumption_measure', 'ACK']

        # with full consumption
        consumption = profile.Consumption(power_source='dc',
                                          board_type='M3',
                                          period='140us',
                                          average='1',
                                          power=True,
                                          voltage=True,
                                          current=True)
        ret = self.protocol.config_consumption(consumption)
        self.sender.assert_called_with(['config_consumption_measure', 'start',
                                        '3.3V', 'p', '1', 'v', '1', 'c', '1',
                                        '-p', '140us', '-a', '1'])
        self.assertEquals(0, ret)


        # consumption without all elements
        consumption = profile.Consumption(power_source='battery',
                                          board_type='M3',
                                          period='8244us',
                                          average='1024',
                                          power=True)
        ret = self.protocol.config_consumption(consumption)
        self.sender.assert_called_with(['config_consumption_measure', 'start',
                                        'BATT', 'p', '1', 'v', '0', 'c', '0',
                                        '-p', '8244us', '-a', '1024'])
        self.assertEquals(0, ret)



    def test_consumption_stop(self):

        self.sender.return_value = ['config_consumption_measure', 'ACK']
        # no consumption object
        ret = self.protocol.config_consumption()
        self.sender.assert_called_with(['config_consumption_measure', 'stop'])
        self.assertEquals(0, ret)
        # power, voltage, current == False
        consumption = profile.Consumption(power_source='dc',
                                          board_type='M3',
                                          period='140us',
                                          average='1')
        ret = self.protocol.config_consumption(consumption)
        self.sender.assert_called_with(['config_consumption_measure', 'stop'])
        self.assertEquals(0, ret)

    def test_start_stop(self):

        self.sender.return_value = ['start', 'ACK']

        ret = self.protocol.start_stop('start', 'dc')
        self.sender.assert_called_with(['start', 'dc'])
        self.assertEquals(0, ret)


        # return NACK
        self.sender.return_value = ['start', 'ACK']
        ret = self.protocol.start_stop('stop', 'dc')
        self.sender.assert_called_with(['stop', 'dc'])
        self.assertEquals(1, ret)

        # return command different type
        self.sender.return_value = ['stop', 'NACK']
        ret = self.protocol.start_stop('stop', 'battery')
        self.sender.assert_called_with(['stop', 'battery'])
        self.assertEquals(1, ret)

    def test_reset_time(self):

        self.sender.return_value = ['reset_time', 'ACK']
        ret = self.protocol.reset_time()
        self.sender.assert_called_with(['reset_time'])
        self.assertEquals(0, ret)

        self.sender.return_value = ['reset_time', 'NACK']
        ret = self.protocol.reset_time()
        self.sender.assert_called_with(['reset_time'])
        self.assertEquals(1, ret)

    def test_led_control(self):

        self.sender.return_value = ['green_led_blink', 'ACK']
        ret = self.protocol.green_led_blink()
        self.sender.assert_called_with(['green_led_blink'])
        self.assertEquals(0, ret)

        self.sender.return_value = ['green_led_on', 'ACK']
        ret = self.protocol.green_led_on()
        self.sender.assert_called_with(['green_led_on'])
        self.assertEquals(0, ret)


class TestProtocolRadio(unittest.TestCase):


    def setUp(self):
        self.protocol = protocol_cn.Protocol(self._sender_wrapper)
        #self.stop_cmd_mock = mock.Mock()
        #self.protocol._stop_radio = self.stop_cmd_mock

        self.sender = mock.Mock()

    def _sender_wrapper(self, command_list):
        return self.sender(command_list)



    def test_config_radio_with_measure(self):
        """ Configure Radio with 'measure' mode """
        radio = profile.Radio("measure", [17,15,11], 100, num_per_channel=10)

        self.protocol._config_radio_measure = mock.Mock()
        self.protocol._config_radio_measure.return_value = 0
        self.protocol._stop_radio = mock.Mock()
        self.protocol._stop_radio.return_value = 0

        ret = self.protocol.config_radio(radio)
        self.assertEquals(0, ret)
        self.assertEquals(0, self.protocol._stop_radio.call_count)
        self.assertEquals(1, self.protocol._config_radio_measure.call_count)

    def test_config_radio_with_none(self):
        """ Configure radio with None Radio profile """

        self.protocol._config_radio_measure = mock.Mock()
        self.protocol._config_radio_measure.return_value = 0
        self.protocol._stop_radio = mock.Mock()
        self.protocol._stop_radio.return_value = 0

        ret = self.protocol.config_radio(None)
        self.assertEquals(0, self.protocol._config_radio_measure.call_count)
        self.assertEquals(1, self.protocol._stop_radio.call_count)

    def test_config_radio_with_invalid_mode(self):
        """ Configure radio with an non supported radio mode """
        radio = profile.Radio("measure", [11], 10, num_per_channel=10)
        radio.mode = "invalid_mode"

        self.assertRaises(NotImplementedError,
                          self.protocol.config_radio, radio)


    def test_config_radio_error_during_config(self):

        radio = profile.Radio("measure", [11], 10, num_per_channel=10)

        self.protocol._config_radio_measure = mock.Mock()
        self.protocol._config_radio_measure.return_value = 0xFF
        self.protocol._stop_radio = mock.Mock()
        self.protocol._stop_radio.return_value = 0

        ret = self.protocol.config_radio(radio)

        self.assertEquals(0xFF, ret)
        self.assertEquals(0, self.protocol._stop_radio.call_count)
        self.assertEquals(1, self.protocol._config_radio_measure.call_count)


    def test_config_radio_measure(self):

        radio = profile.Radio("measure", [17,15,11], 100, num_per_channel=10)

        self.sender.return_value = ['config_radio_measure', 'ACK']
        ret = self.protocol._config_radio_measure(radio)
        self.sender.assert_called_with(['config_radio_measure', '11,15,17',
                                        '100', '10'])
        self.assertEquals(0, ret)



    def test__stop_radio(self):

        self.sender.return_value = ['config_radio_stop', 'ACK']

        ret = self.protocol._stop_radio()

        self.sender.assert_called_with(['config_radio_stop'])
        self.assertEquals(0, ret)

