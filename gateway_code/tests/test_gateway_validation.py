# -*- coding:utf-8 -*-


import unittest
import mock

from gateway_code import gateway_validation


class TestProtocol(unittest.TestCase):


    def setUp(self):
        gateway_manager = mock.Mock()
        self.g_v = gateway_validation.GatewayValidation(gateway_manager)

    @mock.patch('gateway_code.gateway_validation.LOGGER')
    def test_validate(self, mock_logger):

        self.g_v.ret_dict = {'ret': None, 'success':[], 'error':[], 'mac':{}}

        # test validate
        ret_1 = self.g_v._validate(0, 'message_1', ['1', '2'])
        ret_2 = self.g_v._validate(1, 'message_2', ['3', '4'])

        self.assertEquals(0, ret_1)
        self.assertEquals(1, ret_2)

        self.assertTrue('message_1' in self.g_v.ret_dict['success'])
        self.assertTrue('message_2' in self.g_v.ret_dict['error'])

    def test_measures_handler_functions(self):
        """ test measures handler functions """

        self.g_v.keep_all_measures = False
        # no measure
        ret_none = self.g_v._get_measure(timeout=0.0000001)
        self.assertEquals(None, ret_none)

        # one measure
        self.g_v._measures_handler(0)
        ret_zero = self.g_v._get_measure()
        self.assertEquals(0, ret_zero)

        # first measure dropped
        self.g_v._measures_handler('removed')
        self.g_v._measures_handler(1)
        ret_one = self.g_v._get_measure()
        self.assertEquals(1, ret_one)

        self.g_v.keep_all_measures = True
        # keep all measures
        self.g_v._measures_handler(0)
        self.g_v._measures_handler(1)
        ret_zero = self.g_v._get_measure()
        ret_one = self.g_v._get_measure()

        self.assertEquals(0, ret_zero)
        self.assertEquals(1, ret_one)

class TestAutoTestsErrorCases(unittest.TestCase):

    def setUp(self):
        gateway_manager = mock.Mock()
        self.g_v = gateway_validation.GatewayValidation(gateway_manager)

    def test_fail_on_setup(self):
        def setup(*args, **kwargs):
            self.g_v.ret_dict = {'ret': None, 'success':[], 'error':[], 'mac':{}}
            self.g_v.ret_dict['error'].append('setup')
            return 999

        def teardown(*args, **kwargs):
            self.g_v.ret_dict['error'].append('teardown')
            return 1

        self.g_v.setup = mock.Mock(side_effect=setup)

        self.g_v.teardown = mock.Mock(side_effect=teardown)

        ret_dict = self.g_v.auto_tests()

        self.assertEquals(1000, ret_dict['ret'])
        self.assertEquals([], ret_dict['success'])
        self.assertEquals(['setup', 'teardown'], ret_dict['error'])

