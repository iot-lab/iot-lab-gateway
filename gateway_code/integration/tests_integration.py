#! /usr/bin/env python

import gateway_code
import time
import os
import recordtype # mutable namedtuple (for small classes)

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
    }


@patch('gateway_code.openocd_cmd.config.STATIC_FILES_PATH', new=STATIC_DIR)
@patch('gateway_code.gateway_manager.config.FIRMWARES', MOCK_FIRMWARES)
@patch('gateway_code.config.GATEWAY_CONFIG_PATH', CURRENT_DIR + '/config_m3/')
@patch('gateway_code.control_node_interface.CONTROL_NODE_INTERFACE_ARGS', ['-d'])  # print measures
class TestComplexExperimentRunning(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
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


    def setUp(self):
        # get quick access to class attributes
        self.app   = TestComplexExperimentRunning.app
        self.files = TestComplexExperimentRunning.files

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


    @patch('gateway_code.control_node_interface.LOGGER.debug')
    def tests_multiple_complete_experiment(self, m_logger):
        """
        Test a complete experiment 3 times (loooong test)
        Experiment ==
            start
            flash
            reset
            stop
        """

        msg = 'HELLO WORLD\n'

        self.request.files = {'firmware': self.files['control_node']}
        ret = self.app.admin_control_flash()
        self.assertEquals(ret, {'ret':0})

        ret = self.app.admin_control_soft_reset()
        self.assertEquals(ret, {'ret':0})


        for i in range(0, 3):
            m_logger.reset_mock()

            self._rewind_files()

            # start
            self.request.files = {'firmware': self.files['idle'], \
                    'profile':self.files['profile']}
            ret = self.app.exp_start(123, 'clochette')
            self.assertEquals(ret, {'ret':0})

            time.sleep(1)

            # idle firmware, should be no reply
            ret = _send_command_open_node('localhost', 20000, msg)
            self.assertEquals(ret, None)



            # flash
            self.request.files = {'firmware': self.files['echo']}
            ret = self.app.open_flash()
            self.assertEquals(ret, {'ret':0})

            self.app.reset_time()

            # wait node started
            time.sleep(1)

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
            self._rewind_files()
            self.request.files = {'firmware': self.files['echo']}
            ret = self.app.open_flash()
            self.assertNotEquals(ret, {'ret':0})


            #
            # Validate measures consumption
            #

            # measures values in correct range
            calls = [call[0][0].split(' ') for call in m_logger.call_args_list]
            measures = [args[2:] for args in calls if
                        args[0:2] == ['measures_debug:', 'consumption_measure']]
            for measure in measures:
                # no power,  voltage in 3.3V, current not null
                self.assertEquals(0.0, float(measure[1]))
                self.assertTrue(3.0 <= float(measure[2]) <= 3.5)
                self.assertNotEquals(0.0, float(measure[3]))

            # timestamps are in correct order
            timestamps = [self._time_from_args(args) for args in measures]
            sorted = [timestamps[i] <= timestamps[i+1] for (i, _) in
                      enumerate(timestamps[:-1])]
            self.assertTrue(all(sorted))


    @staticmethod
    def _time_from_args(args):
        # args == ['1377265551.811187:5.33661', ...]
        _times_str = args[0].split(':')
        time = float(_times_str[0]) + float(_times_str[1])
        return time


    def tests_invalid_calls(self):
        """
        Test start calls when not needed
            * start when started
            * stop when stopped
        """

        ret = self.app.exp_start(123, 'clochette')
        self.assertEquals(ret, {'ret':0})
        ret = self.app.exp_start(123, 'clochette') # cannot start started exp
        self.assertNotEquals(ret, {'ret':0})

        # stop exp
        ret = self.app.exp_stop()
        self.assertEquals(ret, {'ret':0})

        ret = self.app.exp_stop() # cannot stop stoped exp
        self.assertNotEquals(ret, {'ret':0})


    def tests_invalid_profile_at_start(self):

        self._rewind_files()
        self.request.files = {'profile': self.files['invalid_profile']}
        ret = self.app.exp_start(123, 'clochette')
        self.assertNotEquals(ret, {'ret':0})

        # invalid json
        self._rewind_files()
        self.request.files = {'profile': self.files['invalid_profile_2']}
        ret = self.app.exp_start(123, 'clochette')
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

