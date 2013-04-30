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



@patch('gateway_code.config.STATIC_FILES_PATH', STATIC_DIR)
@patch('gateway_code.gateway_manager.IDLE_FIRMWARE', STATIC_DIR + 'idle.elf')
@patch('gateway_code.gateway_manager.CONTROL_NODE_FIRMWARE', \
        STATIC_DIR + 'control_node.elf')
class TestComplexExperimentRunning(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with patch('gateway_code.config.STATIC_FILES_PATH', STATIC_DIR):
            with patch('gateway_code.gateway_manager.CONTROL_NODE_FIRMWARE', \
                    STATIC_DIR + 'control_node.elf'):
                cls.app = gateway_code.server_rest.GatewayRest(\
                        gateway_code.server_rest.GatewayManager('.'))

        cls.files = {}
        # default files
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


    def tests_multiple_complete_experiment(self):
        """
        Test a complete experiment 3 times (loooong test)
        Experiment ==
            start
            flash
            reset
            stop
        """

        msg = 'HELLO WORLD\n'



        for i in range(0, 3):

            self._rewind_files()

            # start
            self.request.files = {'firmware': self.files['idle'], \
                    'profile':self.files['profile']}
            ret = self.app.exp_start(123, 'clochette')
            assert ret == {'ret':0}

            time.sleep(1)

            # idle firmware, should be no reply
            ret = _send_command_open_node('localhost', 20000, msg)
            assert ret == None



            # flash
            self.request.files = {'firmware': self.files['echo']}
            ret = self.app.open_flash()
            assert ret == {'ret':0}

            # wait node started
            time.sleep(1)

            # echo firmware, should reply what was sent
            ret = _send_command_open_node('localhost', 20000, msg)
            assert ret == msg


            # reset open node
            ret = self.app.open_soft_reset()
            assert ret == {'ret':0}

            # stop exp
            ret = self.app.exp_stop()
            assert ret == {'ret':0}


    def tests_invalid_calls(self):
        """
        Test start calls when not needed
            * start when started
            * stop when stopped
        """

        self.request.files = {'firmware': self.files['idle'], \
                'profile':self.files['default_profile']}
        ret = self.app.exp_start(123, 'clochette')
        assert ret == {'ret':0}


        self._rewind_files()
        ret = self.app.exp_start(123, 'clochette')
        assert ret['ret'] != 0

        # stop exp
        ret = self.app.exp_stop()
        assert ret == {'ret':0}

        ret = self.app.exp_stop()
        assert ret['ret'] != 0




    def tests_invalid_files(self):
        """
        Test invalid calls
            * invalid start
            * invalid flash
        """
        self.request.files = {}
        ret = self.app.exp_start(123, 'clochett')
        assert ret['ret'] != 0

        self.request.files = {'firmware': self.files['idle'], \
                'profile':self.files['profile']}
        ret = self.app.open_flash()
        assert ret['ret'] != 0

