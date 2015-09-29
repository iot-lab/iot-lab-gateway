# -*- coding: utf-8 -*-

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


""" Common integration tests m3/a8 """

# pylint: disable=protected-access
# pylint: disable=too-many-public-methods

import os
import time
import math
from itertools import izip

import mock
from mock import patch
from gateway_code.tests.rest_server_test import query_string

from gateway_code.integration import test_integration_mock
from gateway_code.autotest import autotest
from gateway_code.utils.node_connection import OpenNodeConnection
from gateway_code.common import wait_cond

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) + '/'

USER = 'harter'
EXP_ID = 123
EXP_START = '/exp/start/{exp_id}/{user}'.format(user=USER, exp_id=123)

# Bottle FileUpload class stub


class FileUpload(object):  # pylint: disable=too-few-public-methods

    """ Bottle FileUpload class stub """
    files = {}

    def __init__(self, file_path):
        self.file = None
        self.filename = None
        self.name = None
        self.headers = None

        self.filename = os.path.basename(file_path)
        _ext = os.path.splitext(self.filename)[1]

        try:
            self.name = {
                '.json': 'profile',
                '.elf': 'firmware', '.hex': 'firmware'}[_ext]
        except KeyError:
            raise ValueError("Uknown file type %r: %r" % (_ext, file_path))

        self.file = open(file_path)


def file_tuple(fieldname, file_path):
    """ Return upload_file tuple """
    filename = os.path.basename(file_path)
    with open(file_path) as file_fd:
        content = file_fd.read()

    return (fieldname, filename, content)


class ExperimentRunningMock(test_integration_mock.GatewayCodeMock):

    """ Create environment for running experiments """

    def setUp(self):
        super(ExperimentRunningMock, self).setUp()

        # super(self).cn_measures = []  # will hold control node measures

        # no timeout
        self.request.query = mock.Mock(timeout='')
        self.request.files = {}

        # config experiment and create folder
        self.g_m._create_user_exp_folders(USER, EXP_ID)

    def tearDown(self):
        super(ExperimentRunningMock, self).tearDown()
        self.g_m._destroy_user_exp_folders(USER, EXP_ID)

    @staticmethod
    def send_n_cmds(command, num_times, step=0.5):
        """ Send a command multiple times and return array of answers """
        answers = []
        cmd = command.split()
        for _itr in range(0, num_times):  # pylint:disable=unused-variable
            ans = OpenNodeConnection.send_one_command(cmd)
            ans = ' '.join(ans) if ans is not None else None
            answers.append(ans)
            time.sleep(step)
        return answers


class TestComplexExperimentRunning(ExperimentRunningMock):

    """ Run complete experiment test """
    def setUp(self):
        super(TestComplexExperimentRunning, self).setUp()
        self.request_patcher.stop()

    @patch('gateway_code.control_node.cn_interface.LOGGER.error')
    def test_simple_experiment(self, m_error):
        """ Test simple experiment"""
        board_class = self.board_cfg.board_class

        # The A8 node is really different from the others
        if board_class.TYPE == 'a8':
            self._run_simple_experiment_a8(m_error)
        else:
            self._run_simple_experiment_node(m_error, board_class)

    def _run_simple_experiment_a8(self, moc):  # pylint:disable=unused-argument
        """ Run an experiment for a8 nodes """

        self.assertEquals(0, self.server.post(EXP_START).json['ret'])

        # waiting One minute to try to have complete boot log on debug output
        time.sleep(60)  # maybe do something here later

        self.assertEquals(0, self.server.delete('/exp/stop').json['ret'])

    def _run_simple_experiment_node(self, m_error, board_class):
        """
        Run a simple experiment on a node without profile
        Try the different node features
        """
        msg = 'HELLO WORLD'

        # start exp with idle firmware
        files = [file_tuple('firmware', board_class.FW_IDLE)]
        ret = self.server.post(EXP_START, upload_files=files)
        self.assertEquals(0, ret.json['ret'])

        # wait firmware started
        time.sleep(1)

        # idle firmware, there should be no reply
        self.assertNotIn(msg, self.send_n_cmds('echo %s' % msg, 5))

        # flash echo firmware
        files = [file_tuple('firmware', board_class.FW_AUTOTEST)]
        ret = self.server.post('/open/flash', upload_files=files)
        self.assertEquals(0, ret.json['ret'])
        time.sleep(1)

        # Should echo <message>, do it multiple times for reliability
        self.assertIn(msg, self.send_n_cmds('echo %s' % msg, 5))

        # open node reset and start stop
        self.assertEquals(0, self.server.put('/open/reset').json['ret'])
        self.assertEquals(0, self.server.put('/open/start').json['ret'])
        self.assertEquals(0, self.server.put('/open/stop').json['ret'])

        # stop exp
        self.assertEquals(0, self.server.delete('/exp/stop').json['ret'])

        # Got no error during tests (use call_args_list for printing on error)
        self.assertEquals([], m_error.call_args_list)

        # reset firmware should fail and logger error will be called
        self.assertLessEqual(1, self.server.put('/open/reset').json['ret'])
        self.assertTrue(m_error.called)

    @patch('gateway_code.control_node.cn_interface.LOGGER.error')
    def test_m3_exp_with_measures(self,  # pylint:disable=too-many-locals
                                  m_error):
        """ Run an experiment with measures and profile update """
        board_class = self.board_cfg.board_class
        app_json = 'application/json'

        if 'm3' != board_class.TYPE:
            return
        t_start = time.time()

        files = [file_tuple('firmware', board_class.FW_AUTOTEST)]
        ret = self.server.post(EXP_START, upload_files=files)
        self.assertEquals(0, ret.json['ret'])

        # Copy files for further checking
        exp_files = self.g_m.exp_files.copy()

        # Set first profile
        profile = file_tuple('profile', CURRENT_DIR + 'profile.json')[-1]
        ret = self.server.post('/exp/update', profile, content_type=app_json)
        self.assertEquals(0, ret.json['ret'])

        time.sleep(10)  # wait measures here

        # Remove profile
        ret = self.server.post('/exp/update', content_type=app_json)
        self.assertEquals(0, ret.json['ret'])

        time.sleep(2)  # wait maybe remaining values

        measures = autotest.extract_measures(self.cn_measures)
        self.cn_measures = []

        # # # # # # # # # #
        # Check measures  #
        # # # # # # # # # #

        # Got consumption and radio
        self.assertNotEquals([], measures['consumption']['values'])
        self.assertNotEquals([], measures['radio']['values'])

        # Validate values
        for values in measures['consumption']['values']:
            # no power, voltage in 3.3V, current not null
            self.assertTrue(math.isnan(values[0]))
            self.assertTrue(2.8 <= values[1] <= 3.5)
            self.assertNotEquals(0.0, values[2])
        for values in measures['radio']['values']:
            self.assertIn(values[0], [15, 26])
            self.assertGreaterEqual(-91, values[1])

        # check timestamps are sorted in correct order
        for values in measures.values():
            timestamps = [t_start] + values['timestamps'] + [time.time()]
            _sorted = all([a < b for a, b in izip(timestamps, timestamps[1:])])
            self.assertTrue(_sorted)

        # there should be no new measures since profile update
        # wait 5 more seconds that no measures arrive
        # wait_cond is used as 'check still false'
        wait_cond(5, False, lambda: [] == self.cn_measures)
        self.assertEquals([], self.cn_measures)

        # Stop experiment
        self.assertEquals(0, self.server.delete('/exp/stop').json['ret'])
        # Got no error during tests (use assertEquals for printing result)
        self.assertEquals([], m_error.call_args_list)

        # # # # # # # # # # # # # # # # # # # # # #
        # Test OML Files still exists after stop  #
        #    * radio and conso file exist         #
        # # # # # # # # # # # # # # # # # # # # # #
        for meas_type in ('radio', 'consumption'):
            try:
                os.remove(exp_files[meas_type])
            except IOError:
                self.fail('File should exist %r' % exp_files[meas_type])


class TestExperimentTimeout(ExperimentRunningMock):
    """ Test the 'timeout' feature of experiments """

    def setUp(self):
        super(TestExperimentTimeout, self).setUp()
        self.timeout_mock = mock.Mock(side_effect=self.g_m._timeout_exp_stop)
        patch.object(self.g_m, '_timeout_exp_stop', self.timeout_mock).start()
        self.request_patcher.stop()

    def _safe_exp_is_running(self):
        """ Return experiment state but do it under gateway manager rlock
        It prevents other commands to be still running while checking """
        with self.g_m.rlock:  # No operation running at the same time
            return self.g_m.experiment_is_running

    def test_experiment_with_timeout(self):
        """ Start an experiment with a timeout. """
        extra = query_string('timeout=5')
        ret = self.server.post(EXP_START, extra_environ=extra)
        self.assertEquals(0, ret.json['ret'])

        # Wait max 10 seconds for experiment to have been stopped
        self.assertTrue(wait_cond(10, False, self._safe_exp_is_running))
        self.assertTrue(self.timeout_mock.called)

    def test_exp_stop_removes_timeout(self):
        """ Test exp_stop removes timeout stop """
        extra = query_string('timeout=5')
        ret = self.server.post(EXP_START, extra_environ=extra)
        self.assertEquals(0, ret.json['ret'])
        # Stop to remove timeout
        self.assertEquals(0, self.server.delete('/exp/stop').json['ret'])

        time.sleep(10)  # Ensure that timeout could have occured
        # Timeout never called
        self.assertFalse(self.timeout_mock.called)

    def test__timeout_on_wrong_exp(self):
        """ Test _timeout_exp_stop only stops it's experiment """

        self.assertEquals(0, self.server.post(EXP_START).json['ret'])

        # simulate a previous experiment stop occuring too late
        self.g_m._timeout_exp_stop(exp_id=(EXP_ID - 1), user=USER)
        # still running
        self.assertTrue(self._safe_exp_is_running)

        # cleanup
        self.assertEquals(0, self.server.delete('/exp/stop').json['ret'])


class TestIntegrationOther(ExperimentRunningMock):
    """ Group other tests cases"""

    def setUp(self):
        super(TestIntegrationOther, self).setUp()
        self.request_patcher.stop()

    def test_status(self):
        """ Call the status command """
        ret = self.server.get('/status')
        self.assertEquals(0, ret.json['ret'])

    def tests_non_regular_start_stop(self):
        """ Test start calls when not needed
            * start when started
            * stop when stopped
        """
        stop_mock = mock.Mock(side_effect=self.g_m.exp_stop)
        with patch.object(self.g_m, 'exp_stop', stop_mock):

            # create experiment
            self.assertEquals(0, self.server.post(EXP_START).json['ret'])
            self.assertEquals(stop_mock.call_count, 0)
            # replace current experiment
            self.assertEquals(0, self.server.post(EXP_START).json['ret'])
            self.assertEquals(stop_mock.call_count, 1)

            # stop exp
            self.assertEquals(0, self.server.delete('/exp/stop').json['ret'])
            # exp already stoped no error
            self.assertEquals(0, self.server.delete('/exp/stop').json['ret'])

    def tests_invalid_tty_exp_a8(self):
        """ Test start where tty is not visible """
        if 'a8' != self.board_cfg.board_type:
            return

        c_n = self.g_m.control_node
        with patch.object(c_n, 'open_start', c_n.open_stop):
            # detect error when a8 does not start
            self.assertLessEqual(1, self.server.post(EXP_START).json['ret'])

        # stop and cleanup
        self.assertEquals(0, self.server.delete('/exp/stop').json['ret'])


class TestInvalidCases(test_integration_mock.GatewayCodeMock):
    """ Invalid calls """

    def setUp(self):
        test_integration_mock.GatewayCodeMock.setUp(self)
        self.request_patcher.stop()

    def tests_invalid_profile_at_start(self):
        """ Run experiments with invalid profiles """

        files = [file_tuple('profile', CURRENT_DIR + 'invalid_profile.json')]
        ret = self.server.post(EXP_START, upload_files=files)
        self.assertLessEqual(1, ret.json['ret'])

        files = [file_tuple('profile', CURRENT_DIR + 'invalid_profile_2.json')]
        ret = self.server.post(EXP_START, upload_files=files)
        self.assertLessEqual(1, ret.json['ret'])

    def tests_invalid_files(self):
        """ Test invalid flash files """
        # Only if flash available
        if 'a8' == self.board_cfg.board_type:
            return

        # Flash with a profile
        files = [file_tuple('profile', CURRENT_DIR + 'profile.json')]
        ret = self.server.post('/open/flash', upload_files=files)
        self.assertLessEqual(1, ret.json['ret'])
