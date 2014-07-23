#! /usr/bin/env python

""" Common integration tests M3/A8 """

import os
import time
import math
from itertools import izip
from sys import stderr

import mock
from mock import patch

# all modules should be imported and not only the package
import gateway_code.control_node_interface
import gateway_code.config
import gateway_code.autotest.m3_node_interface
import gateway_code.autotest.autotest

from gateway_code.autotest.autotest import extract_measures

from gateway_code.integration import integration_mock

# W0212 Access to a protected member '_xxx'of a client class
# pylint: disable=protected-access
# pylint: disable=too-many-public-methods

USER = 'harter'


def _send_command_open_node(command, host='localhost', port=20000):
    """ send a command to host/port and wait for an answer as a line """
    import socket

    ret = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock_file = sock.makefile('rw')
        sock.settimeout(5.0)
        sock.send(command)
        ret = sock_file.readline()
    except (socket.timeout, IOError):
        ret = None
    finally:
        sock.close()
    return ret


class TestComplexExperimentRunning(integration_mock.GatewayCodeMock):
    """ Run complete experiment test """

    def setUp(self):
        super(TestComplexExperimentRunning, self).setUp()
        self.cn_measures = []

        # no timeout
        self.request.query = mock.Mock(timeout='')

        # config experiment and create folder
        self.exp_conf = {'user': USER, 'exp_id': 123}
        self.g_m._create_user_exp_folders(**self.exp_conf)

    def tearDown(self):
        super(TestComplexExperimentRunning, self).tearDown()
        self.g_m._destroy_user_exp_folders(**self.exp_conf)

    def test_admin_commands(self):
        """ Try running the admin commands """
        # flash Control Node
        self.request.files = {'firmware': self.files['control_node']}
        ret = self.app.admin_control_flash()
        self.assertEquals(ret, {'ret': 0})
        ret = self.app.admin_control_soft_reset()
        self.assertEquals(ret, {'ret': 0})

    def _measures_handler(self, measure_str):
        """ control node measures Handler """
        gateway_code.control_node_interface.LOGGER.debug(measure_str)
        self.cn_measures.append(measure_str.split(' '))

    @patch('gateway_code.control_node_interface.LOGGER.error')
    def tests_complete_experiments(self, m_error):
        """ Test complete experiment (loooong test) (3 for M3, 1 for A8)"""
        self.g_m.cn_serial.measures_handler = self._measures_handler

        if 'M3' == gateway_code.config.board_type():
            # start
            for _ in range(0, 3):
                m_error.reset_mock()
                self.cn_measures = []
                integration_mock.FileUpload.rewind_all()
                self._run_one_experiment_m3(m_error)

        elif 'A8' == gateway_code.config.board_type():
            m_error.reset_mock()
            self.request.files = {}
            self._run_one_experiment_a8(m_error)

    def _run_one_experiment_a8(self, m_error):
        """ Run an experiment for A8 nodes """

        _ = m_error

        # Run an experiment that does nothing but wait
        # should keep the same user as it's the only one setup
        ret = self.app.exp_start(**self.exp_conf)
        self.assertEquals(ret, {'ret': 0})

        # waiting One minute to try to have complete boot log on debug output
        time.sleep(60)  # maybe do something here later

        ret = self.app.exp_stop()
        self.assertEquals(ret, {'ret': 0})

    def _run_one_experiment_m3(self, m_error):
        """ Run an experiment """

        msg = 'HELLO WORLD\n'
        t_start = time.time()

        #
        # Run an experiment
        #
        self.request.files = {'firmware': self.files['idle'],
                              'profile': self.files['profile']}
        self.assertEquals({'ret': 0}, self.app.exp_start(**self.exp_conf))
        exp_files = self.g_m.exp_desc['exp_files'].copy()

        time.sleep(1)

        # idle firmware, should be no reply
        self.assertIsNone(_send_command_open_node('echo %s' % msg))

        # flash echo firmware
        self.request.files = {'firmware': self.files['m3_autotest']}
        self.assertEquals({'ret': 0}, self.app.open_flash())
        time.sleep(1)

        # test set_time during experiment
        self.app.set_time()

        # echo firmware, should reply what was sent
        # do it multiple times to be sure
        answers = []
        for _ in range(0, 5):
            ret = _send_command_open_node('echo %s' % msg)
            answers.append(ret)
            time.sleep(0.5)
        self.assertIn(msg, answers)

        # open node reset and start stop
        self.assertEquals({'ret': 0}, self.app.open_soft_reset())
        self.assertEquals({'ret': 0}, self.app.open_start())
        self.assertEquals({'ret': 0}, self.app.open_stop())

        # stop exp
        self.assertEquals({'ret': 0}, self.app.exp_stop())

        #
        # Check results
        #
        # Got no error during tests (use assertEquals for printing result)
        self.assertEquals([], m_error.call_args_list)

        # reset firmware should fail
        # logger error will be called
        self.assertNotEquals({'ret': 0}, self.app.open_soft_reset())
        self.assertTrue(m_error.called)

        #
        # Validate measures consumption
        #
        measures = extract_measures(self.cn_measures)

        self.assertNotEquals([], measures['consumption']['values'])
        for values in measures['consumption']['values']:
            # no power, voltage in 3.3V, current not null
            self.assertTrue(math.isnan(values[0]))
            self.assertTrue(2.8 <= values[1] <= 3.5)
            self.assertNotEquals(0.0, values[2])

        self.assertNotEquals([], measures['radio']['values'])
        for values in measures['radio']['values']:
            self.assertIn(values[0], [15, 26])
            self.assertGreaterEqual(-91, values[1])

        # check timestamps are sorted in correct order
        for values in measures.values():
            timestamps = [t_start] + values['timestamps'] + [time.time()]
            _sorted = all([a < b for a, b in izip(timestamps, timestamps[1:])])
            self.assertTrue(_sorted)

        # Test OML Files
        # radio and conso file exist
        for meas_type in ('radio', 'consumption'):
            self.assertTrue(os.path.isfile(exp_files[meas_type]))
            try:
                os.remove(exp_files[meas_type])
            except IOError:
                self.fail('File should exist %r' % exp_files[meas_type])

    def tests_experiment_timeout(self):
        """ Test two experiments with a timeout """
        self.request.files = {}

        # Create measures folder
        for exp_id in ['1234', '2345']:
            self.g_m._create_user_exp_folders(USER, exp_id)

        # Stop after timeout
        self.request.query = mock.Mock(timeout='5')
        self.assertEquals({'ret': 0}, self.app.exp_start(USER, '1234'))
        time.sleep(10)   # Ensure that timeout occured
        self.g_m.rlock.acquire()  # wait calls ended
        self.g_m.rlock.release()
        # experiment should be stopped
        self.assertFalse(self.g_m.experiment_is_running)

        # Stop remove timeout
        self.request.query = mock.Mock(timeout='5')
        self.assertEquals({'ret': 0}, self.app.exp_start(USER, '1234'))
        self.request.query = mock.Mock(timeout='0')
        self.assertEquals({'ret': 0}, self.app.exp_start(USER, '2345'))
        time.sleep(10)   # Ensure that timeout could have occured
        self.g_m.rlock.acquire()  # wait calls ended
        self.g_m.rlock.release()
        # experiment should be stopped
        self.assertTrue(self.g_m.experiment_is_running)
        self.app.exp_stop()

        # Simulate strange case where timeout is called when another experiment
        # is already running
        self.request.query = mock.Mock(timeout='5')
        self.assertEquals({'ret': 0}, self.app.exp_start(USER, '1234'))

        # 'change' experiment
        self.g_m.exp_desc['exp_id'] = '2345'
        time.sleep(10)   # Ensure that timeout could have occured
        self.g_m.rlock.acquire()  # wait calls ended
        self.g_m.rlock.release()
        self.assertTrue(self.g_m.experiment_is_running)

        # Cleanup experiment
        self.g_m.exp_desc['exp_id'] = '1234'
        self.app.exp_stop()

        # Cleanup measures folder
        for exp_id in ['1234', '2345']:
            self.g_m._destroy_user_exp_folders(USER, exp_id)

    def tests_non_regular_start_stop(self):
        """ Test start calls when not needed
            * start when started
            * stop when stopped
        """
        stop_mock = mock.Mock(side_effect=self.g_m.exp_stop)
        with patch.object(self.g_m, 'exp_stop', stop_mock):

            # create experiment
            self.assertEquals(0, self.g_m.exp_start(**self.exp_conf))
            self.assertEquals(stop_mock.call_count, 0)
            # replace current experiment
            self.assertEquals(0, self.g_m.exp_start(**self.exp_conf))
            self.assertEquals(stop_mock.call_count, 1)

            # stop exp
            self.assertEquals(0, self.g_m.exp_stop())
            # exp already stoped no error
            self.assertEquals(0, self.g_m.exp_stop())

    def tests_invalid_tty_exp_a8(self):
        """ Test start where tty is not visible """
        if 'A8' != gateway_code.config.board_type():
            return

        g_m = self.g_m
        g_m.exp_start(**self.exp_conf)

        with patch.object(g_m, 'open_power_start', g_m.open_power_stop):
            # detect error when A8 does not start
            self.assertNotEquals(0, g_m.exp_start(**self.exp_conf))

        # stop and cleanup
        self.assertEquals(0, g_m.exp_stop())


class TestAutoTests(integration_mock.GatewayCodeMock):
    """ Try running autotests on node """

    def test_complete_auto_tests(self):
        """ Test a regular autotest """
        g_m = self.g_m
        # replace stop
        g_m.open_power_stop = mock.Mock(side_effect=g_m.open_power_stop)

        # call using rest
        self.request.query = mock.Mock(channel='22', gps='', flash='1')
        ret_dict = self.app.auto_tests(mode='blink')
        print >> stderr, ret_dict
        self.assertEquals([], ret_dict['error'])
        self.assertTrue('GWT' in ret_dict['mac'])
        self.assertEquals(0, ret_dict['ret'])

        # test that ON still on => should be blinking and answering
        if gateway_code.config.board_type() != 'M3':
            return
        open_serial = gateway_code.autotest.m3_node_interface.OpenNodeSerial()
        open_serial.start()
        self.assertIsNotNone(open_serial.send_command(['get_time']))
        open_serial.stop()

    def test_mode_no_blink_no_radio(self):
        """ Try running autotest without blinking leds and without radio """

        g_v = gateway_code.autotest.autotest.AutoTestManager(self.g_m)
        ret_dict = g_v.auto_tests(channel=None, blink=False)

        self.assertEquals([], ret_dict['error'])
        self.assertEquals(0, ret_dict['ret'])
        # Radio functions not in results
        self.assertNotIn('test_radio_ping_pong', ret_dict['success'])
        self.assertNotIn('rssi_measures', ret_dict['success'])


class TestInvalidCases(integration_mock.GatewayCodeMock):
    """ Invalid calls """

    def tests_invalid_profile_at_start(self):
        """ Run experiments with invalid profiles """

        self.request.files = {'profile': self.files['invalid_profile']}
        self.assertNotEquals({'ret': 0}, self.app.exp_start(USER, 123))

        self.request.files = {'profile': self.files['invalid_profile_2']}
        self.assertNotEquals({'ret': 0}, self.app.exp_start(USER, 123))

    def tests_invalid_files(self):
        """ Test invalid flash files """

        self.request.files = {'profile': self.files['profile']}
        self.assertNotEquals({'ret': 0}, self.app.open_flash())
