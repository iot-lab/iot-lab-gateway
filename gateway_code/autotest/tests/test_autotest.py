# -*- coding:utf-8 -*-


import unittest
import mock

from gateway_code.autotest import autotest


class TestProtocol(unittest.TestCase):


    def setUp(self):
        gateway_manager = mock.Mock()
        self.g_v = autotest.AutoTestManager(gateway_manager)

    @mock.patch('gateway_code.autotest.autotest.LOGGER')
    def test__check(self, mock_logger):

        self.g_v.ret_dict = {'ret': None, 'success':[], 'error':[], 'mac':{}}

        # test validate
        ret_1 = self.g_v._check(0, 'message_1', ['1', '2'])
        ret_2 = self.g_v._check(1, 'message_2', ['3', '4'])

        self.assertEquals(0, ret_1)
        self.assertEquals(1, ret_2)

        self.assertTrue('message_1' in self.g_v.ret_dict['success'])
        self.assertTrue('message_2' in self.g_v.ret_dict['error'])


    @mock.patch('gateway_code.autotest.autotest.LOGGER.debug')
    def test_run_test(self, mock_debug):
        self.g_v.on_serial = mock.Mock()

        self.send_ret = []
        self.g_v.on_serial.send_command.side_effect = \
            lambda x: self.send_ret.pop(0)


        self.send_ret.append(['ACK', 'COMMAND', '3.14'])
        self.send_ret.append(None)
        self.send_ret.append(['NACK', 'COMMAND', '1.414'])

        values = self.g_v._run_test(3, ['test_command'], 'COMMAND',
                                    lambda x: float(x[2]))

        self.assertEquals([3.14], values)
        mock_debug.assert_called_with('%s answer == %r', 'test_command',
                                      ['NACK', 'COMMAND', '1.414'])


class TestAutoTestsErrorCases(unittest.TestCase):

    def setUp(self):
        gateway_manager = mock.Mock()
        self.g_v = autotest.AutoTestManager(gateway_manager)

    @mock.patch('gateway_code.config.board_type', lambda: 'M3')
    #@mock.patch('gateway_code.autotest.config.board_type', lambda: 'M3')
    def test_fail_on_setup_control_node(self):
        def setup(*args, **kwargs):
            self.g_v.ret_dict = {'ret': None, 'success':[], 'error':[], 'mac':{}}
            self.g_v.ret_dict['error'].append('setup')
            raise autotest.FatalError('Setup failed')

        def teardown(*args, **kwargs):
            self.g_v.ret_dict['error'].append('teardown')
            return 1

        self.g_v.setup_control_node = mock.Mock(side_effect=setup)

        self.g_v.teardown = mock.Mock(side_effect=teardown)

        ret_dict = self.g_v.auto_tests()

        self.assertTrue(2 <= ret_dict['ret'])
        self.assertEquals([], ret_dict['success'])
        self.assertEquals(['setup', 'teardown'], ret_dict['error'])


class TestAutotestFatalError(unittest.TestCase):
    def test_fatal_error(self):
        error = autotest.FatalError("error_value")
        self.assertEquals("'error_value'", str(error))

