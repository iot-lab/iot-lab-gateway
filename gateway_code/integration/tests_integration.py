# -*- coding: utf-8 -*-

""" Common integration tests M3/A8 """

# pylint: disable=protected-access
# pylint: disable=too-many-public-methods

import os
import time
import math
from itertools import izip

import mock
from mock import patch

from gateway_code.integration import test_integration_mock
# all modules should be imported and not only the package
import gateway_code.control_node_interface
import gateway_code.config
from gateway_code.common import wait_cond
from gateway_code.autotest.autotest import extract_measures

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


class TestComplexExperimentRunning(test_integration_mock.GatewayCodeMock):
    """ Run complete experiment test """

    def setUp(self):
        super(TestComplexExperimentRunning, self).setUp()
        self.cn_measures = []

        # no timeout
        self.request.query = mock.Mock(timeout='')
        self.request.files = {}

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
                test_integration_mock.FileUpload.rewind_all()
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

    def test_experiment_with_timeout(self):
        """ Start an experiment with a timeout. """
        timeout_mock = mock.Mock(side_effect=self.g_m._timeout_exp_stop)
        with patch.object(self.g_m, '_timeout_exp_stop', timeout_mock):
            self.request.query = mock.Mock(timeout='5')
            self.assertEquals({'ret': 0}, self.app.exp_start(**self.exp_conf))
            # Wait max 10 seconds for experiment to have been stopped
            self.assertTrue(wait_cond(10, False, self._safe_exp_is_running))
            self.assertTrue(timeout_mock.called)

    def test_exp_stop_removes_timeout(self):
        """ Test exp_stop removes timeout stop """
        # Create measures folder
        timeout_mock = mock.Mock(side_effect=self.g_m._timeout_exp_stop)

        # Stop removes timeout
        with patch.object(self.g_m, '_timeout_exp_stop', timeout_mock):
            self.request.query = mock.Mock(timeout='5')
            self.assertEquals({'ret': 0}, self.app.exp_start(**self.exp_conf))
            self.app.exp_stop()

            time.sleep(10)   # Ensure that timeout could have occured
            self.assertFalse(timeout_mock.called)  # not called

    def test__timeout_on_wrong_exp(self):
        """ Test _timeout_exp_stop only stops it's experiment """
        old_exp_conf = self.exp_conf.copy()
        old_exp_conf['exp_id'] -= 1

        self.assertEquals({'ret': 0}, self.app.exp_start(**self.exp_conf))
        # simulate a previous experiment stop occuring too late
        self.g_m._timeout_exp_stop(**old_exp_conf)
        # still running
        self.assertTrue(self._safe_exp_is_running)

        # cleanup
        self.app.exp_stop()

    def _safe_exp_is_running(self):
        """ Return experiment state but do it under gateway manager rlock
        It prevents other commands to be still running while checking """
        with self.g_m.rlock:  # No operation running at the same time
            return self.g_m.experiment_is_running

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


class TestInvalidCases(test_integration_mock.GatewayCodeMock):
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
