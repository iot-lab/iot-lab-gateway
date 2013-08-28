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



class TestProtocolRadio(unittest.TestCase):


    def setUp(self):
        self.protocol = protocol_cn.Protocol(self._sender_wrapper)
        self.stop_cmd_mock = mock.Mock()

        self.protocol.radio_cmd_association = {
                "measure": self.stop_cmd_mock
                }
        self.sender = mock.Mock()

    def _sender_wrapper(self, command_list):
        return self.sender(command_list)



    def test_config_radio(self):
        radio = profile.Radio(power='3dBm',
                              channel=17,
                              mode="measure",
                              frequency=42)
        self.protocol.current_radio_mode = None

        self.protocol._config_radio_signal = mock.Mock()
        self.protocol._config_radio_signal.return_value = 0

        self.protocol._config_radio_measure = mock.Mock()
        self.protocol._config_radio_measure.return_value = 0

        ret = self.protocol.config_radio(radio)

        self.assertEquals(0, ret)
        self.assertEquals(0, self.stop_cmd_mock.call_count)
        self.assertEquals(1, self.protocol._config_radio_signal.call_count)
        self.assertEquals(1, self.protocol._config_radio_measure.call_count)

    def test_config_radio_none(self):
        self.protocol.current_radio_mode = None
        self.protocol._config_radio_signal = mock.Mock()
        self.protocol._config_radio_signal.return_value = 0

        self.protocol._config_radio_measure = mock.Mock()
        self.protocol._config_radio_measure.return_value = 0

        ret = self.protocol.config_radio(None)
        self.assertEquals(0, self.protocol._config_radio_signal.call_count)
        self.assertEquals(0, self.protocol._config_radio_measure.call_count)


    def test_config_radio_error_on_stop(self):
        self.protocol.current_radio_mode = "measure"
        self.stop_cmd_mock.return_value = 42

        self.protocol._config_radio_signal = mock.Mock()
        self.protocol._config_radio_signal.return_value = 666
        self.protocol._config_radio_measure = mock.Mock()
        self.protocol._config_radio_measure.return_value = 0xDEADBEEF

        ret = self.protocol.config_radio(radio=None)

        self.assertEquals(42, ret)
        self.assertEquals(1, self.stop_cmd_mock.call_count)
        self.assertEquals(0, self.protocol._config_radio_signal.call_count)
        self.assertEquals(0, self.protocol._config_radio_measure.call_count)

    def test_config_radio_error_cases(self):


        radio = profile.Radio(power='3dBm',
                              channel=17,
                              mode="measure",
                              frequency=42)

        self.protocol._config_radio_signal = mock.Mock()
        self.protocol._config_radio_signal.return_value = 666
        self.protocol._config_radio_measure = mock.Mock()
        self.protocol._config_radio_measure.return_value = 334

        ret = self.protocol.config_radio(radio)

        self.assertEquals(1000, ret)
        self.assertEquals(0, self.stop_cmd_mock.call_count)
        self.assertEquals(1, self.protocol._config_radio_signal.call_count)
        self.assertEquals(1, self.protocol._config_radio_measure.call_count)




    def test_config_radio_signal(self):

        self.sender.return_value = ['config_radio_signal', 'ACK']

        radio = profile.Radio(power='3dBm',
                              channel=17,
                              mode="measure",
                              frequency=42)

        ret = self.protocol._config_radio_signal(radio)
        self.sender.assert_called_with(['config_radio_signal', '3dBm', '17'])
        self.assertEquals(0, ret)


    def test_config_radio_measure(self):

        self.sender.return_value = ['config_radio_measure', 'ACK']
        ret = self.protocol._config_radio_measure(command='stop')
        self.sender.assert_called_with(['config_radio_measure', 'stop'])
        self.assertEquals(0, ret)


        self.sender.reset_mock()
        self.sender.return_value = ['config_radio_measure', 'ACK']
        ret = self.protocol._config_radio_measure(command='start', frequency=42)
        self.sender.assert_called_with(['config_radio_measure', 'start', '42'])
        self.assertEquals(0, ret)



    def test_config_radio_mode_error_case(self):
        radio = profile.Radio(power='3dBm',
                              channel=17,
                              mode="measure",
                              frequency=42)
        radio.mode = "Not_Implemented_mode"
        self.assertRaises(NotImplementedError,
                          self.protocol._config_radio_mode, radio)






    def test_radio_stop_should_stop_current_mode(self):
        self.stop_cmd_mock.return_value = 0

        self.protocol.current_radio_mode = "measure"
        ret = self.protocol._stop_radio_if_required(radio=None)
        self.assertEquals(1, self.stop_cmd_mock.call_count)
        self.assertEquals(0, ret)
        self.assertEquals(None, self.protocol.current_radio_mode)



    def test_radio_stop_with_fail(self):
        # error during radio stop
        self.stop_cmd_mock.return_value = 42

        self.protocol.current_radio_mode = "measure"
        ret = self.protocol._stop_radio_if_required(radio=None)
        self.assertEquals(1, self.stop_cmd_mock.call_count)
        self.assertEquals(42, ret)
        self.assertEquals("measure", self.protocol.current_radio_mode)


    def test_radio_stop_nothing_to_do(self):
        self.stop_cmd_mock.return_value = 42

        self.protocol.current_radio_mode = None
        ret = self.protocol._stop_radio_if_required(radio=None)
        self.assertEquals(0, self.stop_cmd_mock.call_count)
        self.assertEquals(0, ret)
        self.assertEquals(None, self.protocol.current_radio_mode)

    def test_radio_stop_same_mode(self):
        self.stop_cmd_mock.return_value = 42

        radio = profile.Radio(power='3dBm',
                              channel=17,
                              mode="measure",
                              frequency=42)

        self.protocol.current_radio_mode = "measure"
        ret = self.protocol._stop_radio_if_required(radio)
        self.assertEquals(0, self.stop_cmd_mock.call_count)
        self.assertEquals(0, ret)
        self.assertEquals(radio.mode, self.protocol.current_radio_mode,)

