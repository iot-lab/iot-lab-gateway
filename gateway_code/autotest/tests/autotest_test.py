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


""" Test the autotest module """

import unittest
import mock
import pytest

from gateway_code.autotest import autotest
from gateway_code.tests import utils


# pylint: disable=missing-docstring
# pylint: disable=protected-access
# pylint >= 1.4
# pylint: disable=too-few-public-methods
# pylint: disable=no-member


class TestProtocol(unittest.TestCase):

    def setUp(self):
        mock.patch(utils.READ_CONFIG, utils.read_config_mock('m3')).start()
        gateway_manager = mock.Mock()
        self.g_v = autotest.AutoTestManager(gateway_manager)

    def tearDown(self):
        mock.patch.stopall()

    def test__check(self):
        # test validate
        ret_1 = self.g_v._check(0, 'message_1', ['1', '2'])
        ret_2 = self.g_v._check(1, 'message_2', ['3', '4'])

        self.assertEqual(0, ret_1)
        self.assertEqual(1, ret_2)

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

        self.assertEqual([3.14], values)
        mock_error.assert_called_with('Autotest: %r: %r',
                                      "On Command: ['test_command']",
                                      ['NACK', 'test_command', '1.414'])

    @mock.patch('gateway_code.autotest.autotest.AutoTestManager._run_test')
    def test_get_uid(self, run_test_mock):
        """ Test get_uid autotest function """

        run_test_mock.return_value = ['05D8FF323632483343037109']
        self.assertEqual(0, self.g_v.get_uid())
        self.assertEqual('05D8:FF32:3632:4833:4303:7109',
                         self.g_v.ret_dict['open_node_uid'])

        # error on get_uid
        run_test_mock.return_value = []
        self.assertNotEqual(0, self.g_v.get_uid())


class TestProtocolGPS(unittest.TestCase):

    def setUp(self):
        config = utils.read_config_mock('a8', linux_open_node_type='a8_m3')
        mock.patch(utils.READ_CONFIG, config).start()
        gateway_manager = mock.Mock()
        self.g_v = autotest.AutoTestManager(gateway_manager)

    def tearDown(self):
        mock.patch.stopall()

    def test_test_gps(self):
        with mock.patch.object(self.g_v, '_test_pps_open_node') as test_pps:
            # test with gps disabled
            self.assertEqual(0, self.g_v.test_gps(False))
            self.assertFalse(test_pps.called)

            # Test with gps enabled
            test_pps.return_value = 0
            self.assertEqual(0, self.g_v.test_gps(True))
            self.assertTrue(test_pps.called)

    def test__test_pps_open_node(self):
        pps_get_values = []

        def _on_call(args):
            cmd = args[0]
            if cmd == 'test_pps_start':
                return (0, ['ACK', 'test_pps_start'])
            if cmd == 'test_pps_stop':
                return (0, ['ACK', 'test_pps_stop'])
            if cmd == 'test_pps_get':
                return pps_get_values.pop(0)

            raise ValueError('Unknown command %r' % cmd)

        with mock.patch.object(self.g_v, '_on_call', _on_call):
            pps_get_values = [(0, ['ACK', 'test_pps_get', '0', 'pps']),
                              (0, ['ACK', 'test_pps_get', '3', 'pps'])]
            self.assertEqual(0, self.g_v._test_pps_open_node(10))

            pps_get_values = []
            self.assertNotEqual(0, self.g_v._test_pps_open_node(0))

            with pytest.raises(ValueError) as exc:
                self.g_v._test_pps_open_node_invalid()
            assert 'Unknown command' in str(exc)


class TestAutotestChecker(unittest.TestCase):

    TESTED_FEATURES = set()

    def setUp(self):
        self.func = mock.Mock()
        self.on_class = mock.Mock()
        self.cn_class = mock.Mock()
        self.linux_on_class = mock.Mock()
        self.TESTED_FEATURES.clear()

    def function(self, *args, **kwargs):
        """ Should mock a real function to let 'wraps' work """
        self.func(self, *args, **kwargs)

    def test_autotest_checker(self):

        self.on_class.AUTOTEST_AVAILABLE = ['echo', 'get_time']
        self.cn_class.FEATURES = []
        self.linux_on_class = None

        # Should call the function
        # func_cmd == decorated function
        func_cmd = autotest.autotest_checker('echo')(self.function)
        func_cmd(self)
        self.assertTrue(self.func.called)
        self.func.reset_mock()

        func_cmd = autotest.autotest_checker('get_time')(self.function)
        func_cmd(self)
        self.assertTrue(self.func.called)
        self.func.reset_mock()

        func_cmd = autotest.autotest_checker('echo', 'get_time')(self.function)
        func_cmd(self)
        self.assertTrue(self.func.called)
        self.func.reset_mock()

        # Not calling the function
        func_cmd = autotest.autotest_checker('unknown')(self.function)
        func_cmd(self)
        self.assertFalse(self.func.called)
        self.func.reset_mock()

        func_cmd = autotest.autotest_checker('echo', 'unknown')(self.function)
        func_cmd(self)
        self.assertFalse(self.func.called)
        self.func.reset_mock()


class TestAutoTestsErrorCases(unittest.TestCase):

    def setUp(self):
        mock.patch(utils.READ_CONFIG, utils.read_config_mock('m3')).start()

        gateway_manager = mock.Mock()
        self.g_v = autotest.AutoTestManager(gateway_manager)

    def tearDown(self):
        mock.patch.stopall()

    def test_fail_on_setup_control_node(self):

        def setup():
            self.g_v.ret_dict['error'].append('setup')
            raise autotest.FatalError('Setup failed')

        def teardown(blink):  # pylint:disable=unused-argument
            self.g_v.ret_dict['error'].append('teardown')
            return 1

        self.g_v.setup_control_node = mock.Mock(side_effect=setup)
        self.g_v.teardown = mock.Mock(side_effect=teardown)

        ret_dict = self.g_v.auto_tests()

        self.assertTrue(ret_dict['ret'] >= 2)
        self.assertEqual([], ret_dict['success'])
        self.assertEqual(['setup', 'teardown'], ret_dict['error'])

    @mock.patch('gateway_code.autotest.autotest.AutoTestManager.'
                '_set_results_leds')
    def test_fatal_error_leds(self, leds):
        assert self.g_v.set_result_leds(0) == 0
        leds.side_effect = autotest.FatalError("Leds Error")
        assert self.g_v.set_result_leds(0) == 1

    @mock.patch('gateway_code.autotest.autotest.AutoTestManager._check')
    def test_assert(self, check):
        ret = 1
        check.return_value = ret
        with pytest.raises(autotest.FatalError) as exc_info:
            assert self.g_v._assert(1, "noop", "err_log", "err_msg") == ret
        assert exc_info.type is autotest.FatalError
        assert "err_msg" in str(exc_info.value)
