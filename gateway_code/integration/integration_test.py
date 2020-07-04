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


""" Common integration tests """

# pylint: disable=protected-access
# pylint: disable=too-many-public-methods
from __future__ import print_function

import os
import os.path
import time
import math
import subprocess
import logging
from threading import Thread

import pytest
import mock
from mock import patch
from testfixtures import LogCapture

from gateway_code.tests.rest_server_test import query_string

from gateway_code.integration import test_integration_mock
from gateway_code.autotest import autotest
from gateway_code.utils.node_connection import OpenNodeConnection
from gateway_code.common import wait_cond, abspath, wait_tty, wait_no_tty
from gateway_code.common import object_attr_has

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) + '/'

USER = 'harter'
EXP_ID = 123
EXP_START = '/exp/start/{exp_id}/{user}'.format(user=USER, exp_id=123)

GDB_CMD = 'gdb' if os.uname()[4] == 'armv7l' else 'gdb-multiarch'

APP_JSON = 'application/json'
GATEWAY_LOGGER = logging.getLogger('gateway_code')


def file_tuple(fieldname, file_path):
    """ Return upload_file tuple """
    filename = os.path.basename(file_path)
    with open(file_path) as file_fd:
        content = file_fd.read()

    return (fieldname, filename, content)


CN_FEATURES_ATTR = 'board_cfg.cn_class.FEATURES'


class ExperimentRunningMock(test_integration_mock.GatewayCodeMock):

    """ Create environment for running experiments """

    def setUp(self):
        super(ExperimentRunningMock, self).setUp()
        # config experiment and create folder
        self.g_m._create_user_exp_folders(USER, EXP_ID)
        self.log_error = LogCapture('gateway_code', level=logging.ERROR)

    def tearDown(self):
        super(ExperimentRunningMock, self).tearDown()
        self.g_m._destroy_user_exp_folders(USER, EXP_ID)
        self.log_error.uninstall()

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

    def control_node_has(self, *features):
        """Checks that control_node has given `features`."""
        return object_attr_has(self, CN_FEATURES_ATTR, features)


class TestComplexExperimentRunning(ExperimentRunningMock):
    """ Run complete experiment test """

    def test_simple_experiment(self):
        """ Test simple experiment"""
        board_class = self.board_cfg.board_class

        # The Linux node is really different from the others
        if board_class.TYPE == 'a8' or board_class.TYPE == 'rpi3':
            self._run_simple_experiment_linux_node()
        else:
            self._run_simple_experiment_node(board_class)

    def _run_simple_experiment_linux_node(self):
        """ Run an experiment for Linux nodes """

        self.assertEqual(0, self.server.post(EXP_START).json['ret'])

        # waiting One minute to try to have complete boot log on debug output
        time.sleep(60)  # maybe do something here later

        self.assertEqual(0, self.server.delete('/exp/stop').json['ret'])

    def _run_simple_experiment_node(self, board_class):
        """
        Run a simple experiment on a node without profile
        Try the different node features
        """
        # start exp with idle firmware
        files = [file_tuple('firmware', board_class.FW_IDLE)]
        ret = self.server.post(EXP_START, upload_files=files)
        self.assertEqual(0, ret.json['ret'])

        # wait firmware started
        time.sleep(1)

        # idle firmware, there should be no reply
        self._check_node_echo(echo=False)

        # flash echo firmware
        ret = self._flash(board_class.FW_AUTOTEST)
        self.assertEqual(0, ret.json['ret'])

        # Should echo <message>
        self._check_node_echo(echo=True)

        # open node reset and start stop
        self.assertEqual(0, self.server.put('/open/reset').json['ret'])
        if self.control_node_has('open_node_power'):
            self.assertEqual(0, self.server.put('/open/stop').json['ret'])
            self.assertEqual(0, self.server.put('/open/start').json['ret'])

        # It is normal to fail if you flash just after starting a node
        # In these tests, I want the node to be "ready" so I ensure that
        wait_no_tty(self.g_m.open_node.TTY, timeout=10)
        wait_tty(self.g_m.open_node.TTY, GATEWAY_LOGGER, timeout=15)

        time.sleep(1)  # wait firmware started

        # Some node can leave their serial port dirty (st-lrwan1 for example)
        if hasattr(board_class, "DIRTY_SERIAL") and board_class.DIRTY_SERIAL:
            # Clear log error
            self.log_error.clear()

        # No log error
        self.log_error.check()

        # Check debug
        self._check_debug(board_class)
        self.log_error.clear()

        if self.control_node_has('open_node_power'):
            # Stop should work with stopped node
            self.assertEqual(0, self.server.put('/open/stop').json['ret'])
        # stop exp
        self.assertEqual(0, self.server.delete('/exp/stop').json['ret'])

        # Got no error during tests (use call_args_list for printing on error)
        self.log_error.check()

        if self.control_node_has('open_node_power'):
            # reset firmware should fail and logger error will be called
            self.assertLessEqual(1, self.server.put('/open/reset').json['ret'])
            self.assertNotEqual('', str(self.log_error))

    def _flash(self, firmware=None):
        """Flash firmware."""
        if firmware:
            files = [file_tuple('firmware', firmware)]
            ret = self.server.post('/open/flash', upload_files=files)
        else:
            ret = self.server.put('/open/flash/idle')
        time.sleep(1)
        return ret

    def _check_node_echo(self, echo=True, msg='HELLO WORLD', tries=5):
        """Check that nodes echo or not."""

        # do it multiple times for reliability
        ret_list = self.send_n_cmds('echo %s' % msg, tries)

        # Two different commands to have more verbosity on error
        if echo:
            self.assertIn(msg, ret_list)
        else:
            self.assertNotIn(msg, ret_list)

    def _check_debug(self, board_class):
        if (not hasattr(board_class, 'debug_stop') or  # no debug
                # Only openocd debug tested here (arm)
                not hasattr(board_class, 'OPENOCD_CFG_FILE')):
            return

        firmware = abspath(board_class.FW_AUTOTEST)
        gdb_cmd = [
            GDB_CMD,
            '-ex', 'set confirm off',
            '-ex', 'target remote localhost:3333',
            '-ex', 'monitor reset halt',
            '-ex', 'monitor flash write_image erase %s' % firmware,
            '-ex', 'monitor reset init',
            '-ex', 'monitor reset run',
            '-ex', 'quit',
        ]

        # Flash idle firmware
        ret = self._flash()
        self.assertEqual(0, ret.json['ret'])

        # idle firmware, there should be no reply
        self._check_node_echo(echo=False)

        # Start debugger
        ret = self.server.put('/open/debug/start')
        self.assertEqual(0, ret.json['ret'])

        # Flash autotest firmware
        ret = subprocess.call(gdb_cmd, stderr=subprocess.STDOUT)
        self.assertEqual(0, ret)
        time.sleep(1)

        # Autotest fw should be running
        self._check_node_echo(echo=True)

        # Flash idle firmware should fail
        ret = self._flash()
        self.assertNotEqual(0, ret.json['ret'])

        # No flash, Autotest fw should be still running
        self._check_node_echo(echo=True)

        # Stop debugger
        ret = self.server.put('/open/debug/stop')
        self.assertEqual(0, ret.json['ret'])

        # Make sure the node can be reflashed after debug session is done
        time.sleep(1)
        ret = self._flash()
        self.assertEqual(0, ret.json['ret'])

    def test_m3_exp_invalid_fw_target(self):
        """Run an experiment with an invalid firmware."""
        if self.board_cfg.board_class.TYPE != 'm3':
            pytest.skip("Not an M3")

        # Invalid firmware for m3
        node_z1 = CURRENT_DIR + 'node.z1'

        with patch.object(self.g_m.open_node, 'flash') as flash_mock:
            flash_mock.return_value = 0

            files = [file_tuple('firmware', node_z1)]
            ret = self.server.post(EXP_START, upload_files=files)

            # Error and flash not called
            self.assertNotEqual(0, ret.json['ret'])
            self.assertFalse(flash_mock.called)

        ret = self.server.delete('/exp/stop')
        self.assertEqual(0, ret.json['ret'])

    def test_m3_flash_inval_fw(self):
        """Flash an invalid firmware during an experiment."""
        if self.board_cfg.board_class.TYPE != 'm3':
            pytest.skip("Not an M3")

        ret = self.server.post(EXP_START)
        self.assertEqual(0, ret.json['ret'])

        # Invalid firmware for m3
        node_z1 = CURRENT_DIR + 'node.z1'
        with patch.object(self.g_m.open_node, 'flash') as flash_mock:
            flash_mock.return_value = 0
            ret = self._flash(node_z1)
            # Error and flash not called
            self.assertNotEqual(0, ret.json['ret'])
            self.assertFalse(flash_mock.called)

        ret = self.server.delete('/exp/stop')
        self.assertEqual(0, ret.json['ret'])

    def _update_profile(self, profilefilename=None, assert_ret=True):
        """Update profile with given 'profilename' file."""
        if profilefilename is not None:
            profile = file_tuple('profile', CURRENT_DIR + profilefilename)[-1]
        else:
            profile = ''

        ret = self.server.post('/exp/update', profile, content_type=APP_JSON)
        if assert_ret:
            self.assertEqual(0, ret.json['ret'])
        return ret

    def test_m3_exp_with_measures(self):  # pylint:disable=too-many-locals
        """ Run an experiment with measures and profile update """

        if self.board_cfg.cn_type != 'iotlab':
            pytest.skip("Not an iotlab control node (requires consumption and "
                        "radio features)")

        if self.board_cfg.board_class.TYPE != 'm3':
            pytest.skip("Not an M3")

        t_start = time.time()

        files = [
            file_tuple('firmware', self.board_cfg.board_class.FW_AUTOTEST),
        ]
        ret = self.server.post(EXP_START, upload_files=files)
        self.assertEqual(0, ret.json['ret'])

        # Copy files for further checking
        exp_files = self.g_m.exp_files.copy()

        # Set a profile for 10s, remove it and wait remaining measures
        self._update_profile('profile.json')
        time.sleep(10)
        self._update_profile(None)
        time.sleep(2)

        measures = autotest.extract_measures(self.cn_measures)
        self.cn_measures = []

        # # # # # # # # # #
        # Check measures  #
        # # # # # # # # # #

        # Got consumption and radio
        self.assertNotEqual([], measures['consumption']['values'])
        self.assertNotEqual([], measures['radio']['values'])

        # Validate values
        for values in measures['consumption']['values']:
            # no power, voltage in 3.3V, current not null
            self.assertTrue(math.isnan(values[0]))
            self.assertTrue(2.8 <= values[1] <= 3.5)
            self.assertNotEqual(0.0, values[2])
        for values in measures['radio']['values']:
            self.assertIn(values[0], [15, 26])
            self.assertLessEqual(-91, values[1])

        # check timestamps are sorted in correct order
        for values in measures.values():
            timestamps = [t_start] + values['timestamps'] + [time.time()]
            _sorted = all([a < b for a, b in zip(timestamps, timestamps[1:])])
            self.assertTrue(_sorted)

        # there should be no new measures since profile update
        # wait 5 more seconds that no measures arrive
        # wait_cond is used as 'check still false'
        wait_cond(5, False, lambda: [] == self.cn_measures)
        self.assertEqual([], self.cn_measures)

        # Stop experiment
        self.assertEqual(0, self.server.delete('/exp/stop').json['ret'])
        # Got no error during tests (use assertEquals for printing result)
        self.log_error.check()

        # # # # # # # # # # # # # # # # # # # # # #
        # Test OML Files still exists after stop  #
        #    * radio and conso file exist         #
        # # # # # # # # # # # # # # # # # # # # # #
        for meas_type in ('radio', 'consumption'):
            assert os.path.isfile(exp_files[meas_type])
            os.remove(exp_files[meas_type])

    def test_exp_with_fastest_measures(self):
        """ Run an experiment with fastest measures."""

        # This test requires consumption feature from control_node
        if self.board_cfg.cn_type != 'iotlab':
            pytest.skip("Not an iotlab control node (requires consumption)")

        # Max profile and firmware if possible
        files = []
        if (self.board_cfg.board_class.TYPE != 'a8' and
                self.board_cfg.board_class.TYPE != 'rpi3'):
            files.append(file_tuple('firmware',
                                    self.board_cfg.board_class.FW_AUTOTEST))

        # Disable cn debug, too fast to print at the same time
        self.g_m.control_node.cn_serial.measures_debug = None

        # Start
        ret = self.server.post(EXP_START, upload_files=files)
        self.assertEqual(0, ret.json['ret'])
        # Copy files for further checking
        exp_files = self.g_m.exp_files.copy()

        self._update_profile('profile_max.json')

        time.sleep(30)

        # When updating profile at full speed
        # Update profile may break, but consumption is still stopped.
        # just ignore errors on the first one here
        self.log_error.check()
        if self._update_profile(None, False):
            time.sleep(1)

            # No error on second _update_profile
            self.log_error.clear()
            self._update_profile(None)
            self.log_error.check()
        time.sleep(2)  # wait maybe remaining values

        # Stop experiment
        self.assertEqual(0, self.server.delete('/exp/stop').json['ret'])

        # Got no error during tests (use assertEquals for printing result)
        if (self.board_cfg.board_class.TYPE != 'a8' and
                self.board_cfg.board_class.TYPE != 'rpi3'):
            # On Linux nodes, ignore error 'Boot failed in time:'
            self.log_error.check()

        # Observed number of measures
        # No real reasons, just verifying that it at least the same
        for meas_type, num_meas in (('radio', 1000), ('consumption', 50000)):
            num_lines = len(open(exp_files[meas_type]).readlines())
            print('num measures lines: %s: %d' % (meas_type, num_lines))
            print('num measures ref: %s: %d' % (meas_type, num_meas))
            # Was failing some times, disable
            # self.assertTrue(num_meas < num_lines)


class TestManagerLocked(ExperimentRunningMock):
    """Test that when manager is locked raises error 503."""
    def test_concurrent_requests(self):
        """Test running a new experiment when manager is stuck."""
        thr_blocking = Thread(target=self.server.get, args=('/sleep/5',))
        thr_blocking.start()
        time.sleep(0.5)
        try:
            # RestServer busy with 'sleep', cannot start a new experiment
            # Error 503
            error_status = 503
            self.server.post(EXP_START, status=error_status)
        finally:
            thr_blocking.join()


class TestExperimentTimeout(ExperimentRunningMock):
    """ Test the 'timeout' feature of experiments """

    def setUp(self):
        super(TestExperimentTimeout, self).setUp()
        self.timeout_mock = mock.Mock(side_effect=self.g_m._timeout_exp_stop)
        patch.object(self.g_m, '_timeout_exp_stop', self.timeout_mock).start()

    def _safe_exp_is_running(self):
        """ Return experiment state but do it under gateway manager rlock
        It prevents other commands to be still running while checking """
        with self.g_m.rlock:  # No operation running at the same time
            return self.g_m.experiment_is_running

    def test_experiment_with_timeout(self):
        """ Start an experiment with a timeout. """
        extra = query_string('timeout=5')
        ret = self.server.post(EXP_START, extra_environ=extra)
        self.assertEqual(0, ret.json['ret'])

        # Wait max 10 seconds for experiment to have been stopped
        self.assertTrue(wait_cond(10, False, self._safe_exp_is_running))
        self.assertTrue(self.timeout_mock.called)

    def test_exp_stop_removes_timeout(self):
        """ Test exp_stop removes timeout stop """
        extra = query_string('timeout=5')
        ret = self.server.post(EXP_START, extra_environ=extra)
        self.assertEqual(0, ret.json['ret'])
        # Stop to remove timeout
        self.assertEqual(0, self.server.delete('/exp/stop').json['ret'])

        time.sleep(10)  # Ensure that timeout could have occured
        # Timeout never called
        self.assertFalse(self.timeout_mock.called)

    def test__timeout_on_wrong_exp(self):
        """ Test _timeout_exp_stop only stops it's experiment """

        self.assertEqual(0, self.server.post(EXP_START).json['ret'])

        # simulate a previous experiment stop occuring too late
        self.g_m._timeout_exp_stop(exp_id=(EXP_ID - 1), user=USER)
        # still running
        self.assertTrue(self._safe_exp_is_running)

        # cleanup
        self.assertEqual(0, self.server.delete('/exp/stop').json['ret'])


class TestIntegrationOther(ExperimentRunningMock):
    """ Group other tests cases"""

    def test_status(self):
        """ Call the status command """
        ret = self.server.get('/status')
        self.assertEqual(0, ret.json['ret'])

    def test_non_regular_start_stop(self):
        """ Test start calls when not needed
            * start when started
            * stop when stopped
        """
        stop_mock = mock.Mock(side_effect=self.g_m.exp_stop)
        with patch.object(self.g_m, 'exp_stop', stop_mock):

            # create experiment
            self.assertEqual(0, self.server.post(EXP_START).json['ret'])
            self.assertEqual(stop_mock.call_count, 0)
            # replace current experiment
            self.assertEqual(0, self.server.post(EXP_START).json['ret'])
            self.assertEqual(stop_mock.call_count, 1)

            # stop exp
            self.assertEqual(0, self.server.delete('/exp/stop').json['ret'])
            # exp already stoped no error
            self.assertEqual(0, self.server.delete('/exp/stop').json['ret'])

    def test_invalid_tty_exp_linux_node(self):
        """ Test start where tty is not visible """
        if (self.board_cfg.board_type != 'a8' and
                self.board_cfg.board_type != 'rpi3'):
            pytest.skip("Only for Linux nodes")

        c_n = self.g_m.control_node
        with patch.object(c_n, 'open_start', c_n.open_stop):
            # detect error when Linux node does not start
            self.assertLessEqual(1, self.server.post(EXP_START).json['ret'])

        # stop and cleanup
        self.assertEqual(0, self.server.delete('/exp/stop').json['ret'])


class TestInvalidCases(test_integration_mock.GatewayCodeMock):
    """ Invalid calls """

    def test_invalid_profile_at_start(self):
        """ Run experiments with invalid profiles """

        files = [file_tuple('profile', CURRENT_DIR + 'invalid_profile.json')]
        ret = self.server.post(EXP_START, upload_files=files)
        self.assertLessEqual(1, ret.json['ret'])

        files = [file_tuple('profile', CURRENT_DIR + 'invalid_profile_2.json')]
        ret = self.server.post(EXP_START, upload_files=files)
        self.assertLessEqual(1, ret.json['ret'])

    def test_invalid_files(self):
        """ Test invalid flash files """
        # Only if flash available
        if (self.board_cfg.board_type == 'a8' or
                self.board_cfg.board_type == 'rpi3'):
            pytest.skip("Not for Linux nodes")

        # Flash with a profile
        files = [file_tuple('profile', CURRENT_DIR + 'profile.json')]
        ret = self.server.post('/open/flash', upload_files=files)
        self.assertLessEqual(1, ret.json['ret'])
