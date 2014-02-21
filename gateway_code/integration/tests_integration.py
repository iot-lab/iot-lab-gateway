#! /usr/bin/env python

import gateway_code
import time
import os
import recordtype # mutable namedtuple (for small classes)
import shutil
import math

import mock
from mock import patch
import unittest

# pylint: disable=C0103,R0904

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) + '/'
STATIC_DIR  = CURRENT_DIR + 'static/' # using the 'static' symbolic link
STABLE_FIRMWARE = STATIC_DIR + 'control_node.elf'


# Bottle FileUpload class stub
FileUpload = recordtype.recordtype('FileUpload', \
        ['file', 'name', 'filename', ('headers', None)])


import socket
def _send_command_open_node(host, port, command):
    """
    send a command to host/port and wait for an answer as a line
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock_file = sock.makefile('rw')
    sock.settimeout(5.0)
    ret = None
    try:
        sock.send(command)
        ret = sock_file.readline()
    except socket.timeout:
        ret = None
    finally:
        sock.close()
    return ret


MOCK_FIRMWARES = {
    'idle': STATIC_DIR + 'idle.elf',
    'control_node': STATIC_DIR + 'control_node.elf',
    'm3_autotest': STATIC_DIR + 'm3_autotest.elf',
    'a8_autotest': STATIC_DIR + 'a8_autotest.elf'
    }


class GatewayCodeMock(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.static_patcher = patch('gateway_code.openocd_cmd.config.STATIC_FILES_PATH', new=STATIC_DIR)
        cls.static_patcher.start()

        cls.firmwares_patcher = patch('gateway_code.config.FIRMWARES', MOCK_FIRMWARES)
        cls.firmwares_patcher.start()
        cls.cn_interface_patcher = patch('gateway_code.control_node_interface.CONTROL_NODE_INTERFACE_ARGS', ['-d'])  # print measures
        cls.cn_interface_patcher.start()

        cls.app = gateway_code.server_rest.GatewayRest(\
                gateway_code.server_rest.GatewayManager('.'))

        cls.files = {}
        # default files
        cls.files['control_node'] = FileUpload(\
                file = open(STATIC_DIR + 'control_node.elf', 'rb'),
                name = 'firmware', filename = 'control_node.elf')

        cls.files['idle'] = FileUpload(\
                file = open(STATIC_DIR + 'idle.elf', 'rb'),
                name = 'firmware', filename = 'idle.elf')
        cls.files['default_profile'] = FileUpload(\
                file = open(STATIC_DIR + 'default_profile.json', 'rb'),
                name = 'profile', filename = 'default_profile.json')


        # test specific files
        cls.files['echo'] = FileUpload(\
                file = open(CURRENT_DIR + 'serial_echo.elf', 'rb'),
                name = 'firmware', filename = 'serial_echo.elf')

        cls.files['profile'] = FileUpload(\
                file = open(CURRENT_DIR + 'profile.json', 'rb'),
                name = 'profile', filename = 'profile.json')
        cls.files['invalid_profile'] = FileUpload(\
                file = open(CURRENT_DIR + 'invalid_profile.json', 'rb'),
                name = 'profile', filename = 'invalid_profile.json')
        cls.files['invalid_profile_2'] = FileUpload(\
                file = open(CURRENT_DIR + 'invalid_profile_2.json', 'rb'),
                name = 'profile', filename = 'invalid_profile_2.json')


    @classmethod
    def tearDownClass(cls):
        for file_obj in cls.files.itervalues():
            file_obj.file.close()
        cls.static_patcher.stop()
        cls.firmwares_patcher.stop()
        cls.cn_interface_patcher.stop()


    def setUp(self):
        # get quick access to class attributes
        self.app   = type(self).app
        self.files = type(self).files

        self.request_patcher = patch('gateway_code.server_rest.request')
        self.request = self.request_patcher.start()

        self._rewind_files()


    def _rewind_files(self):
        """
        Rewind files at start position
        """
        for file_obj in self.files.itervalues():
            file_obj.file.seek(0)


    def tearDown(self):
        self.request_patcher.stop()
        self.app.exp_stop() # just in case, post error cleanup



class TestComplexExperimentRunning(GatewayCodeMock):

    def setUp(self):
        super(TestComplexExperimentRunning, self).setUp()
        self.exp_conf = {
            'user': 'harter',
            'exp_id': 123,
            'node_id': gateway_code.config.hostname()
            }
        self.request.files = {'firmware': self.files['control_node']}
        ret = self.app.admin_control_flash()
        self.assertEquals(ret, {'ret':0})

        ret = self.app.admin_control_soft_reset()
        self.assertEquals(ret, {'ret':0})

        measure_path = gateway_code.config.MEASURES_PATH
        self.radio_path = measure_path.format(type='radio', **self.exp_conf)
        self.conso_path = measure_path.format(type='consumption', **self.exp_conf)
        for measure_file in (self.conso_path, self.radio_path):
            try:
                folder_path = os.path.dirname(measure_file)
                os.makedirs(folder_path)
            except os.error as err:
                pass

    def tearDown(self):
        super(TestComplexExperimentRunning, self).tearDown()
        # remove exp folder
        # ...../exp_id/consumption/node_name.oml
        shutil.rmtree(os.path.dirname(os.path.dirname(self.conso_path)))


    @patch('gateway_code.control_node_interface.LOGGER.error')
    def tests_multiple_complete_experiment(self, m_error):
        """
        Test a complete experiment 3 times (loooong test)
        Experiment ==
            start
            flash
            reset
            stop
        """
        self.error_is_fail = True
        def error(msg, *args, **kwargs):
            if self.error_is_fail:
                self.fail("LOGGER.error(%r,%r,%r))" % (msg, args, kwargs))

        m_error.side_effect = error

        msg = 'HELLO WORLD\n'
        measure_mock = mock.Mock()
        measure_mock.side_effect = gateway_code.control_node_interface.LOGGER.debug

        self.app.gateway_manager.cn_serial.measures_handler = measure_mock

        for i in range(0, 3):
            measure_mock.reset_mock()
            self._rewind_files()


            # start
            self.request.files = {
                'firmware': self.files['idle'],
                'profile':self.files['profile']
                }
            ret = self.app.exp_start(self.exp_conf['exp_id'], self.exp_conf['user'])

            self.assertEquals(ret, {'ret':0})
            time.sleep(1)


            # idle firmware, should be no reply
            ret = _send_command_open_node('localhost', 20000, msg)
            self.assertEquals(ret, None)

            # flash echo firmware
            self.request.files = {'firmware': self.files['echo']}
            ret = self.app.open_flash()
            self.assertEquals(ret, {'ret':0})
            time.sleep(1)

            # test reset_time
            self.app.reset_time()

            # echo firmware, should reply what was sent
            ret = _send_command_open_node('localhost', 20000, msg)
            self.assertEquals(ret, msg)

            ret = self.app.open_soft_reset()
            self.assertEquals(ret, {'ret':0})

            ret = self.app.open_start()
            self.assertEquals(ret, {'ret':0})
            ret = self.app.open_stop()
            self.assertEquals(ret, {'ret':0})

            # stop exp
            ret = self.app.exp_stop()
            self.assertEquals(ret, {'ret':0})


            # flash firmware should fail
            self.error_is_fail = False  # disable logger.error mock
            self._rewind_files()
            self.request.files = {'firmware': self.files['echo']}
            ret = self.app.open_flash()
            self.assertNotEquals(ret, {'ret':0})
            self.error_is_fail = True  # reenable mock

            #
            # Validate measures consumption
            #

            # filter calls that are consumption meausures
            calls = [call[0][0].split(' ') for call in measure_mock.call_args_list]
            measures = [args[2:] for args in calls if
                        ['measures_debug:', 'consumption_measure'] == args[0:2]]

            for measure in measures:
                # no power,  voltage in 3.3V, current not null
                self.assertTrue(math.isnan(float(measure[1])))
                self.assertTrue(2.8 <= float(measure[2]) <= 3.5)
                self.assertNotEquals(0.0, float(measure[3]))

            # timestamps are in correct order
            timestamps = [float(args[0]) for args in measures]
            is_sorted = [timestamps[i] <= timestamps[i+1] for (i, _) in
                      enumerate(timestamps[:-1])]
            self.assertTrue(all(is_sorted))

            # radio file is already removed
            try:
                with open(self.radio_path): pass
            except IOError:
                pass
            else:
                self.fail('%r file should be not exist' % self.radio_path)
            # conso file exists
            try:
                with open(self.conso_path): pass
                os.remove(self.conso_path)
            except IOError:
                self.fail('File should exist %r' % self.radio_path)




class TestAutoTests(GatewayCodeMock):

    def test_complete_auto_tests(self):
        # replace stop
        g_m = self.app.gateway_manager
        real_stop = g_m.open_power_stop
        mock_stop = mock.Mock(side_effect=real_stop)

        g_m.open_power_stop = mock_stop

        self.request.query = mock.Mock()
        self.request.query.channel = '22'
        self.request.query.gps = ''

        # call using rest
        ret_dict = self.app.auto_tests(mode='blink')
        ret = ret_dict['ret']
        success = ret_dict['success']
        errors = ret_dict['error']
        mac_addresses = ret_dict['mac']

        import sys
        print >> sys.stderr, ret_dict
        self.assertEquals([], errors)
        self.assertTrue('GWT' in mac_addresses)
        self.assertEquals(0, ret)

        self.assertEquals(0, g_m.open_power_stop.call_count)

        # test that ON still on => should be blinking and answering
        if gateway_code.config.board_type() == 'M3':
            open_serial = gateway_code.autotest.m3_node_interface.\
                OpenNodeSerial()
            open_serial.start()
            answer = open_serial.send_command(['get_time'])
            self.assertNotEquals(None, answer)
            open_serial.stop()

    def test_mode_no_blink_no_radio(self):

        g_v = gateway_code.autotest.autotest.AutoTestManager(
                self.app.gateway_manager)
        # radio functions
        g_v.test_radio_ping_pong = mock.Mock()
        g_v.test_radio_with_rssi = mock.Mock()

        ret_dict = g_v.auto_tests(channel=None, blink=False)
        self.assertEquals([], ret_dict['error'])
        self.assertEquals(0, ret_dict['ret'])
        self.assertEquals(0, g_v.test_radio_ping_pong.call_count)
        self.assertEquals(0, g_v.test_radio_with_rssi.call_count)


class TestInvalidCases(GatewayCodeMock):

    def tests_invalid_calls(self):
        """
        Test start calls when not needed
            * start when started
            * stop when stopped
        """

        # create measures_dir
        for measure_type in ('consumption', 'radio'):
            try:
                os.mkdir('/tmp/%s/' % measure_type)
            except OSError as err:
                pass

        with mock.patch('gateway_code.config.MEASURES_PATH',
                        '/tmp/{type}/{node_id}.oml'):
            ret = self.app.exp_start(123, 'harter')
            self.assertEquals(ret, {'ret':0})
            ret = self.app.exp_start(123, 'harter') # cannot start started exp
            self.assertNotEquals(ret, {'ret':0})

            # stop exp
            ret = self.app.exp_stop()
            self.assertEquals(ret, {'ret':0})

            ret = self.app.exp_stop() # cannot stop stoped exp
            self.assertNotEquals(ret, {'ret':0})

        # remove measures_dir
        for measure_type in ('consumption', 'radio'):
            try:
                os.rmdir('/tmp/%s/' % measure_type)
            except OSError as err:
                self.fail()


    def tests_invalid_profile_at_start(self):

        self._rewind_files()
        self.request.files = {'profile': self.files['invalid_profile']}
        ret = self.app.exp_start(123, 'harter')
        self.assertNotEquals(ret, {'ret':0})

        # invalid json
        self._rewind_files()
        self.request.files = {'profile': self.files['invalid_profile_2']}
        ret = self.app.exp_start(123, 'harter')
        self.assertNotEquals(ret, {'ret':0})



    def tests_invalid_files(self):
        """
        Test invalid calls
            * invalid start
            * invalid flash
        """

        self.request.files = {'profile':self.files['profile']}
        ret = self.app.open_flash()
        self.assertNotEquals(ret, {'ret':0})

