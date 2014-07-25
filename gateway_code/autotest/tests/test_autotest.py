# -*- coding:utf-8 -*-

""" Test the autotest module """

import unittest
import mock

from gateway_code.autotest import autotest

# pylint: disable=missing-docstring
# pylint: disable=too-many-public-methods
# pylint: disable=protected-access


class TestProtocol(unittest.TestCase):

    def setUp(self):
        gateway_manager = mock.Mock()
        self.g_v = autotest.AutoTestManager(gateway_manager)
        self.g_v.ret_dict = {'ret': None, 'success': [], 'error': [],
                             'mac': {}}

    def test__check(self):
        # test validate
        ret_1 = self.g_v._check(0, 'message_1', ['1', '2'])
        ret_2 = self.g_v._check(1, 'message_2', ['3', '4'])

        self.assertEquals(0, ret_1)
        self.assertEquals(1, ret_2)

        self.assertTrue('message_1' in self.g_v.ret_dict['success'])
        self.assertTrue('message_2' in self.g_v.ret_dict['error'])

    @mock.patch('gateway_code.autotest.autotest.LOGGER.error')
    def test_run_test(self, mock_error):
        self.g_v.on_serial = mock.Mock()

        send_ret = []
        self.g_v.on_serial.send_command.side_effect = \
            lambda x: send_ret.pop(0)

        send_ret.append(['ACK', 'test_command', '3.14'])
        send_ret.append(None)
        send_ret.append(['NACK', 'test_command', '1.414'])

        values = self.g_v._run_test(3, ['test_command'], lambda x: float(x[2]))

        self.assertEquals([3.14], values)
        mock_error.assert_called_with('Autotest: %r: %r',
                                      "On Command: ['test_command']",
                                      ['NACK', 'test_command', '1.414'])

    @mock.patch('gateway_code.autotest.autotest.AutoTestManager._run_test')
    def test_get_uid(self, run_test_mock):
        """ Test get_uid autotest function """

        run_test_mock.return_value = ['05D8FF323632483343037109']
        self.assertEquals(0, self.g_v.get_uid())
        self.assertEquals('05D8:FF32:3632:4833:4303:7109',
                          self.g_v.ret_dict['open_node_m3_uid'])

        # error on get_uid
        run_test_mock.return_value = []
        self.assertNotEquals(0, self.g_v.get_uid())


class TestAutoTestsErrorCases(unittest.TestCase):

    def setUp(self):
        gateway_manager = mock.Mock()
        self.g_v = autotest.AutoTestManager(gateway_manager)

    @mock.patch('gateway_code.config.board_type', lambda: 'unknown')
    def test_invalid_board_type(self):
        ret_dict = self.g_v.auto_tests()
        self.assertNotEquals(0, ret_dict['ret'])
        self.assertEquals([], ret_dict['success'])
        self.assertEquals(['board_type'], ret_dict['error'])

    @mock.patch('gateway_code.config.board_type', lambda: 'M3')
    def test_fail_on_setup_control_node(self):
        def setup():
            self.g_v.ret_dict['error'].append('setup')
            raise autotest.FatalError('Setup failed')

        def teardown(_):
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
