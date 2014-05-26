#! /usr/bin/env python

""" Common integration tests M3/A8 """

import os
import time
import shutil
import math
import recordtype

import mock
from mock import patch
import unittest

import gateway_code
# pylint: disable=C0103,R0904

# Bottle FileUpload class stub
FileUpload = recordtype.recordtype(
    'FileUpload', ['file', 'name', 'filename', ('headers', None)])

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) + '/'
STATIC_DIR = CURRENT_DIR + 'static/'  # using the 'static' symbolic link
MOCK_FIRMWARES = {
    'idle': STATIC_DIR + 'idle.elf',
    'control_node': STATIC_DIR + 'control_node.elf',
    'm3_autotest': STATIC_DIR + 'm3_autotest.elf',
    'a8_autotest': STATIC_DIR + 'a8_autotest.elf'
    }


class GatewayCodeMock(unittest.TestCase):
    """ gateway_code mock for integration tests  """

    @classmethod
    def setUpClass(cls):
        cls.static_patcher = patch(
            'gateway_code.openocd_cmd.config.STATIC_FILES_PATH',
            new=STATIC_DIR)
        cls.static_patcher.start()

        cls.static_patcher_2 = patch(
            'gateway_code.autotest.open_a8_interface.config.STATIC_FILES_PATH',
            new=STATIC_DIR)
        cls.static_patcher_2.start()

        cls.firmwares_patcher = patch('gateway_code.config.FIRMWARES',
                                      MOCK_FIRMWARES)
        cls.firmwares_patcher.start()
        cls.cn_interface_patcher = patch(
            'gateway_code.control_node_interface.CONTROL_NODE_INTERFACE_ARGS',
            ['-d'])  # print measures
        cls.cn_interface_patcher.start()

        g_m = gateway_code.server_rest.GatewayManager('.')
        g_m.setup()
        cls.app = gateway_code.server_rest.GatewayRest(g_m)

        cls.files = {}
        # default files
        cls.files['control_node'] = FileUpload(
            file=open(STATIC_DIR + 'control_node.elf', 'rb'),
            name='firmware', filename='control_node.elf')

        cls.files['idle'] = FileUpload(
            file=open(STATIC_DIR + 'idle.elf', 'rb'),
            name='firmware', filename='idle.elf')
        cls.files['default_profile'] = FileUpload(
            file=open(STATIC_DIR + 'default_profile.json', 'rb'),
            name='profile', filename='default_profile.json')

        # test specific files
        cls.files['echo'] = FileUpload(
            file=open(CURRENT_DIR + 'serial_echo.elf', 'rb'),
            name='firmware', filename='serial_echo.elf')

        cls.files['profile'] = FileUpload(
            file=open(CURRENT_DIR + 'profile.json', 'rb'),
            name='profile', filename='profile.json')
        cls.files['invalid_profile'] = FileUpload(
            file=open(CURRENT_DIR + 'invalid_profile.json', 'rb'),
            name='profile', filename='invalid_profile.json')
        cls.files['invalid_profile_2'] = FileUpload(
            file=open(CURRENT_DIR + 'invalid_profile_2.json', 'rb'),
            name='profile', filename='invalid_profile_2.json')

    @classmethod
    def tearDownClass(cls):
        for file_obj in cls.files.itervalues():
            file_obj.file.close()
        cls.static_patcher.stop()
        cls.static_patcher_2.stop()
        cls.firmwares_patcher.stop()
        cls.cn_interface_patcher.stop()

    def setUp(self):
        # get quick access to class attributes
        self.app = type(self).app
        self.files = type(self).files

        self.request_patcher = patch('gateway_code.server_rest.request')
        self.request = self.request_patcher.start()
        self.request.query = mock.Mock(timeout='0')  # no timeout by default

        self._rewind_files()

    def _rewind_files(self):
        """
        Rewind files at start position
        """
        for file_obj in self.files.itervalues():
            file_obj.file.seek(0)

    def tearDown(self):
        self.request_patcher.stop()
        self.app.exp_stop()  # just in case, post error cleanup

def _send_command_open_node(host, port, command):
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


class TestComplexExperimentRunning(GatewayCodeMock):
    """ Run complete experiment test """

    def setUp(self):
        super(TestComplexExperimentRunning, self).setUp()
        self.exp_conf = {
            'user': 'harter',
            'exp_id': 123,
            'node_id': gateway_code.config.hostname()
            }
        self.request.files = {'firmware': self.files['control_node']}
        ret = self.app.admin_control_flash()
        self.assertEquals(ret, {'ret': 0})

        ret = self.app.admin_control_soft_reset()
        self.assertEquals(ret, {'ret': 0})

        self.cn_measures = []

        # no timeout
        self.request.query = mock.Mock(timeout='')

        measure_path = gateway_code.config.MEASURES_PATH
        self.radio_path = measure_path.format(type='radio', **self.exp_conf)
        self.conso_path = measure_path.format(
            type='consumption', **self.exp_conf)
        for measure_file in (self.conso_path, self.radio_path):
            try:
                folder_path = os.path.dirname(measure_file)
                os.makedirs(folder_path)
            except os.error:
                pass

    def tearDown(self):
        super(TestComplexExperimentRunning, self).tearDown()
        # remove exp folder
        # ...../exp_id/consumption/node_name.oml
        try:
            shutil.rmtree(os.path.dirname(os.path.dirname(self.conso_path)))
        except OSError:
            pass

    def _measures_handler(self, measure_str):
        """ control node measures Handler """
        gateway_code.control_node_interface.LOGGER.debug(measure_str)
        self.cn_measures.append(measure_str.split(' '))

    @patch('gateway_code.control_node_interface.LOGGER.error')
    def tests_complete_experiments(self, m_error):
        """ Test complete experiment (loooong test) (3 for M3, 1 for A8)"""
        self.app.gateway_manager.cn_serial.measures_handler = \
            self._measures_handler

        if 'M3' == gateway_code.config.board_type():
            for _ in range(0, 3):

                m_error.reset_mock()
                self.cn_measures = []
                self._rewind_files()

                # start
                self.request.files = {
                    'firmware': self.files['idle'],
                    'profile': self.files['profile']
                    }
                self._run_one_experiment_m3(m_error)

        elif 'A8' == gateway_code.config.board_type():
                m_error.reset_mock()
                self.request.files = {}
                self._run_one_experiment_a8(m_error)

    def _run_one_experiment_a8(self, m_error):
        """ Run an experiment for A8 nodes """

        # Run an experiment that does nothing but wait
        # should keep the same user as it's the only one setup
        ret = self.app.exp_start(123, self.exp_conf['user'])
        self.assertEquals(ret, {'ret': 0})

        # waiting One minute to try to have complete boot log on debug output
        time.sleep(60)  # maybe do something here later

        ret = self.app.exp_stop()
        self.assertEquals(ret, {'ret': 0})

    def _run_one_experiment_m3(self, m_error):
        """ Run an experiment """

        msg = 'HELLO WORLD\n'
        t_before_start = time.time()

        #
        # Run an experiment
        #
        ret = self.app.exp_start(
            self.exp_conf['exp_id'], self.exp_conf['user'])

        self.assertEquals(ret, {'ret': 0})
        time.sleep(1)

        # idle firmware, should be no reply
        ret = _send_command_open_node('localhost', 20000, msg)
        self.assertEquals(ret, None)

        # flash echo firmware
        self.request.files = {'firmware': self.files['echo']}
        ret = self.app.open_flash()
        self.assertEquals(ret, {'ret': 0})
        time.sleep(1)

        # test set_time during experiment
        self.app.set_time()

        # echo firmware, should reply what was sent
        # do it multiple times to be sure
        answers = []
        for _ in range(0, 5):
            ret = _send_command_open_node('localhost', 20000, msg)
            answers.append(ret)
            time.sleep(0.5)
        self.assertIn(msg, answers)

        # open node reset and start stop
        ret = self.app.open_soft_reset()
        self.assertEquals(ret, {'ret': 0})

        ret = self.app.open_start()
        self.assertEquals(ret, {'ret': 0})
        ret = self.app.open_stop()
        self.assertEquals(ret, {'ret': 0})

        # stop exp
        ret = self.app.exp_stop()
        self.assertEquals(ret, {'ret': 0})

        #
        # Check results
        #
        # Got no error during tests (use assertEquals for printing result)
        self.assertEquals([], m_error.call_args_list)

        # flash firmware should fail
        # logger error will be called
        ret = self.app.open_soft_reset()
        self.assertNotEquals(ret, {'ret': 0})
        self.assertTrue(m_error.called)

        #
        # Validate measures consumption
        #
        # filter consumption meausures
        measures = []
        for meas in self.cn_measures:
            if 'consumption_measure' != meas[1]:
                continue
            measures.append(tuple([float(val) for val in meas[2:6]]))

        for meas in measures:
            # no power,  voltage in 3.3V, current not null
            self.assertTrue(math.isnan(meas[1]))
            self.assertTrue(2.8 <= meas[2] <= 3.5)
            self.assertNotEquals(0.0, meas[3])

        # check timestamps are sorted in correct order
        timestamps = ([t_before_start] + [args[0] for args in measures] +
                      [time.time()])

        self.assertTrue(
            all([a < b for a, b in zip(timestamps, timestamps[1:])]))

        #
        # Test OML Files
        #
        # radio file is already removed
        self.assertRaises(IOError, open, self.radio_path)
        # conso file exists
        try:
            open(self.conso_path).close()
            os.remove(self.conso_path)
        except IOError:
            self.fail('File should exist %r' % self.radio_path)


    def tests_experiment_timeout(self):
        """ Test two experiments with a timeout """
        self._rewind_files()
        self.request.files = {}

        # Create measures folder
        for exp_id in ['1234', '2345']:
            _exp_conf = dict(self.exp_conf)
            _exp_conf['exp_id'] = exp_id
            measure_path = gateway_code.config.MEASURES_PATH
            radio_path = measure_path.format(type='radio', **_exp_conf)
            conso_path = measure_path.format(type='consumption', **_exp_conf)
            for measure_file in (conso_path, radio_path):
                try:
                    os.makedirs(os.path.dirname(measure_file))
                except os.error:
                    pass


        # Stop after timeout
        self.request.query = mock.Mock(timeout='5')
        ret = self.app.exp_start('1234', self.exp_conf['user'])
        self.assertEquals(ret, {'ret': 0})
        time.sleep(10)   # Ensure that timeout occured
        self.app.gateway_manager.rlock.acquire()  # wait calls ended
        self.app.gateway_manager.rlock.release()
        # experiment should be stopped
        self.assertFalse(self.app.gateway_manager.experiment_is_running)


        # Stop remove timeout
        self.request.query = mock.Mock(timeout='5')
        ret = self.app.exp_start('1234', self.exp_conf['user'])
        self.assertEquals(ret, {'ret': 0})
        self.request.query = mock.Mock(timeout='0')
        ret = self.app.exp_start('2345', self.exp_conf['user'])
        self.assertEquals(ret, {'ret': 0})
        time.sleep(10)   # Ensure that timeout could have occured
        self.app.gateway_manager.rlock.acquire()  # wait calls ended
        self.app.gateway_manager.rlock.release()
        # experiment should be stopped
        self.assertTrue(self.app.gateway_manager.experiment_is_running)
        ret = self.app.exp_stop()


        # Simulate strange case where timeout is called when another experiment
        # is already running
        self.request.query = mock.Mock(timeout='5')
        ret = self.app.exp_start('1234', self.exp_conf['user'])
        self.assertEquals(ret, {'ret': 0})

        self.app.gateway_manager.exp_id = '2345'  # 'change' experiment
        time.sleep(10)   # Ensure that timeout could have occured
        self.app.gateway_manager.rlock.acquire()  # wait calls ended
        self.app.gateway_manager.rlock.release()
        self.assertTrue(self.app.gateway_manager.experiment_is_running)

        self.app.gateway_manager.exp_id = '1234'  # recover experiment
        ret = self.app.exp_stop()


        # Cleanup measures folder
        for exp_id in ['1234', '1235']:
            try:
                shutil.rmtree(os.path.dirname(os.path.dirname(conso_path)))
            except OSError:
                pass


class TestAutoTests(GatewayCodeMock):
    """ Try running autotests on node """

    def test_complete_auto_tests(self):
        """ Test a regular autotest """
        # replace stop
        g_m = self.app.gateway_manager
        real_stop = g_m.open_power_stop
        mock_stop = mock.Mock(side_effect=real_stop)

        g_m.open_power_stop = mock_stop

        self.request.query = mock.Mock()
        self.request.query.channel = '22'
        self.request.query.gps = ''
        self.request.query.flash = ''

        # call using rest
        ret_dict = self.app.auto_tests(mode='blink')
        ret = ret_dict['ret']
        errors = ret_dict['error']
        mac_addresses = ret_dict['mac']

        import sys
        print >> sys.stderr, ret_dict
        self.assertEquals([], errors)
        self.assertTrue('GWT' in mac_addresses)
        self.assertEquals(0, ret)

        # test that ON still on => should be blinking and answering
        if gateway_code.config.board_type() == 'M3':
            open_serial = gateway_code.autotest.m3_node_interface.\
                OpenNodeSerial()
            open_serial.start()
            answer = open_serial.send_command(['get_time'])
            self.assertNotEquals(None, answer)
            open_serial.stop()

    def test_mode_no_blink_no_radio(self):
        """ Try running autotest without blinking leds and without radio """

        g_v = gateway_code.autotest.autotest.AutoTestManager(
            self.app.gateway_manager)

        # radio functions
        with patch.object(g_v, 'test_radio_ping_pong'):
            with patch.object(g_v, 'test_radio_with_rssi'):
                ret_dict = g_v.auto_tests(channel=None, blink=False)
                self.assertEquals([], ret_dict['error'])
                self.assertEquals(0, ret_dict['ret'])
                self.assertEquals(0, g_v.test_radio_ping_pong.call_count)
                self.assertEquals(0, g_v.test_radio_with_rssi.call_count)


class TestUncommonCasesGatewayManager(GatewayCodeMock):
    """ Uncommon cases """

    def setUp(self):
        # create measures_dir
        self.measures_path_patcher = patch('gateway_code.config.MEASURES_PATH',
                                           '/tmp/{type}/{node_id}.oml')
        self.measures_path_patcher.start()
        self.user_log_path_patcher = patch('gateway_code.config.USER_LOG_PATH',
                                           '/tmp/{node_id}.oml')
        self.user_log_path_patcher.start()

        for measure_type in ('consumption', 'radio'):
            try:
                os.mkdir('/tmp/%s/' % measure_type)
            except OSError:
                pass


    def tearDown(self):
        self.measures_path_patcher.stop()
        self.user_log_path_patcher.stop()
        # remove measures_dir
        for measure_type in ('consumption', 'radio'):
            shutil.rmtree('/tmp/%s/' % measure_type, ignore_errors=True)

    def tests_non_regular_start_stop_calls(self):
        """ Test start calls when not needed
            * start when started
            * stop when stopped
        """
        stop_mock = mock.Mock(side_effect=self.app.gateway_manager.exp_stop)
        with patch.object(self.app.gateway_manager, 'exp_stop', stop_mock):

            ret = self.app.gateway_manager.exp_start(12, 'harter')
            self.assertEquals(ret, 0)
            self.assertEquals(self.app.gateway_manager.exp_id, 12)
            self.assertEquals(stop_mock.call_count, 0)

            # replace current experiment
            ret = self.app.gateway_manager.exp_start(12, 'harter')
            self.assertEquals(ret, 0)
            self.assertEquals(self.app.gateway_manager.exp_id, 12)
            self.assertEquals(stop_mock.call_count, 1)

            # stop exp
            ret = self.app.gateway_manager.exp_stop()
            self.assertEquals(ret, 0)

            # exp already stoped no error
            ret = self.app.gateway_manager.exp_stop()
            self.assertEquals(ret, 0)

    def tests_invalid_tty_state_at_start_stop_for_A8(self):
        """  Test start/stop calls where A8 tty is in invalid state
        Test a start call where tty is not visible
        Followed by a stop call that will have it's tty not disappeared
        """

        if 'A8' != gateway_code.config.board_type():
            return

        with patch.object(self.app.gateway_manager, 'open_power_start',
                          mock.Mock(return_value=0)):
            ret = self.app.gateway_manager.exp_start(12, 'harter')
            self.assertNotEquals(ret, 0)
        ret = self.app.gateway_manager.exp_stop()
        self.assertEquals(ret, 0)


        ret = self.app.gateway_manager.exp_start(12, 'harter')
        self.assertEquals(ret, 0)
        with patch.object(self.app.gateway_manager, 'open_power_stop',
                          mock.Mock(return_value=0)):
            ret = self.app.gateway_manager.exp_stop()
            self.assertNotEquals(ret, 0)

        # real cleanup
        ret = self.app.gateway_manager.exp_start(12, 'harter')
        self.assertEquals(ret, 0)
        ret = self.app.gateway_manager.exp_stop()
        self.assertEquals(ret, 0)


class TestInvalidCases(GatewayCodeMock):
    """ Invalid calls """

    @patch('gateway_code.config.USER_LOG_PATH', '/tmp/{node_id}.oml')
    def tests_invalid_profile_at_start(self):
        """ Run experiments with invalid profiles """

        self.request.files = {'profile': self.files['invalid_profile']}
        ret = self.app.exp_start(123, 'harter')
        self.assertNotEquals(ret, {'ret': 0})

        self.request.files = {'profile': self.files['invalid_profile_2']}
        ret = self.app.exp_start(123, 'harter')
        self.assertNotEquals(ret, {'ret': 0})

    def tests_invalid_files(self):
        """
        Test invalid calls
            * invalid start
            * invalid flash
        """

        self.request.files = {'profile': self.files['profile']}
        ret = self.app.open_flash()
        self.assertNotEquals(ret, {'ret': 0})

