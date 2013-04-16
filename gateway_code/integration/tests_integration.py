#! /usr/bin/env python

import gateway_code
import time
import os

from mock import patch

import unittest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) + '/'

class _FileUpload(object):
    def __init__(self, file_obj, name, filename, headers=None):
        self.file     = file_obj
        self.name     = name
        self.filename = filename
        self.headers  = headers


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
        args = ['tests', 'localhost', '8080']
        cls.app = gateway_code.server_rest.GatewayRest(\
                gateway_code.server_rest.GatewayManager('.'))

    def setUp(self):
        self.app = TestComplexExperimentRunning.app

        self.request_patcher = patch('gateway_code.server_rest.request')
        self.request = self.request_patcher.start()

        self.idle = _FileUpload(\
                file_obj = open(CURRENT_DIR + 'simple_idle.elf', 'rb'),
                name = 'firmware', filename = 'simple_idle.elf')

        self.echo = _FileUpload(\
                file_obj = open(CURRENT_DIR + 'serial_echo.elf', 'rb'),
                name = 'firmware', filename = 'serial_echo.elf')

        self.profile = _FileUpload(\
                file_obj = open(CURRENT_DIR + 'profile.json', 'rb'),
                name = 'profile', filename = 'profile.json')
        self.reduced_profile = _FileUpload(\
                file_obj = open(CURRENT_DIR + 'reduced_profile.json', 'rb'),
                name = 'profile', filename = 'reduced_profile.json')


        self.files = [self.idle.file, self.echo.file, \
                self.profile.file, self.reduced_profile.file]


    def _reload_files(self):
        for file_obj in self.files:
            file_obj.seek(0)


    def tearDown(self):
        self.request.stop()
        for file_obj in self.files:
            file_obj.close()


    def tests_complete_experiment(self):
        """
        Test a complete experiment
            start
            flash
            reset
            stop
        """

        msg = 'HELLO WORLD\n'


        # start
        self.request.files = {'firmware': self.idle, 'profile':self.profile}
        ret = self.app.exp_start(123, 'clochette')
        assert ret == {'ret':0}

        time.sleep(5)

        # idle firmware, should be no reply
        ret = _send_command_open_node('localhost', 20000, msg)
        assert ret == None


        # flash
        self.request.files = {'firmware': self.echo}
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

        self.request.files = {'firmware': self.idle, 'profile':self.reduced_profile}
        ret = self.app.exp_start(123, 'clochette')
        assert ret == {'ret':0}


        self._reload_files()
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

        self.request.files = {'firmware': self.idle, 'profile':self.profile}
        ret = self.app.open_flash()
        assert ret['ret'] != 0

