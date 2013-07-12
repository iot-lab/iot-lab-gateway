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
        consumption = profile.Consumption(source='3.3V',
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
        consumption = profile.Consumption(source='BATT',
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
        consumption = profile.Consumption(source='3.3V',
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



