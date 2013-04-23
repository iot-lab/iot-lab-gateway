#! /usr/bin/env python

import gateway_code
import time
import os

import recordtype # mutable namedtuple (for to small classes)

from mock import patch

import unittest

# pylint: disable=C0103,R0904


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) + '/'
STABLE_FIRMWARE = os.environ['HOME'] + '/elf_m3c/' + 'main_stable.elf'

# Bottle FileUpload class stub
FileUpload = recordtype('FileUpload', \
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


class TestComplexExperimentRunning(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = gateway_code.server_rest.GatewayRest(\
                gateway_code.server_rest.GatewayManager('.'))

        cls.files = {}
        cls.files['idle'] = FileUpload(\
                file_obj = open(CURRENT_DIR + 'simple_idle.elf', 'rb'),
                name = 'firmware', filename = 'simple_idle.elf')

        cls.files['echo'] = FileUpload(\
                file_obj = open(CURRENT_DIR + 'serial_echo.elf', 'rb'),
                name = 'firmware', filename = 'serial_echo.elf')

        cls.files['profile'] = FileUpload(\
                file_obj = open(CURRENT_DIR + 'profile.json', 'rb'),
                name = 'profile', filename = 'profile.json')
        cls.files['reduced_profile'] = FileUpload(\
                file_obj = open(CURRENT_DIR + 'reduced_profile.json', 'rb'),
                name = 'profile', filename = 'reduced_profile.json')

        cls.files['control_node'] = FileUpload(\
                file_obj = open(STABLE_FIRMWARE, 'rb'),
                name = 'profile', filename = 'control_node.elf')

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
        for file_obj in self.files:
            file_obj.file.seek(0)


    def tearDown(self):
        self.request_patcher.stop()
        for file_obj in self.files:
            file_obj.file.close()


    def tests_complete_experiment(self):
        """
        Test a complete experiment
            start
            flash
            reset
            stop
        """

        msg = 'HELLO WORLD\n'

        # flash control node before starting
        self.request.files = {'firmware': self.files['control_node']}
        ret = self.app.admin_control_flash()
        assert ret == {'ret':0}

        self.request.files = {}
        ret = self.app.admin_control_soft_reset()
        assert ret == {'ret':0}


        # start
        self.request.files = {'firmware': self.files['idle'], \
                'profile':self.files['profile']}
        ret = self.app.exp_start(123, 'clochette')
        assert ret == {'ret':0}

        time.sleep(5)

        # idle firmware, should be no reply
        ret = _send_command_open_node('localhost', 20000, msg)
        assert ret == None


        # flash
        self.request.files = {'firmware': self.files['echo']}
        ret = self.app.open_flash()
        assert ret == {'ret':0}

        # wait node started
        time.sleep(2)

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
                'profile':self.files['reduced_profile']}
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

