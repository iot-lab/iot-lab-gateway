#! /usr/bin/env python

import gateway_code
#from gateway_code import server_rest
import time
import os
import sys

from mock import patch

import unittest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) + '/'

class _FileUpload(object):
    def __init__(self, file, name, filename, headers=None):
        self.file     = file
        self.name     = name
        self.filename = filename
        self.headers  = headers

class TestComplexExperimentRunning(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        args = ['tests', 'localhost', '8080']
        cls.app = gateway_code.server_rest.GatewayRest(gateway_code.server_rest.GatewayManager('.'))

    def setUp(self):
        self.app = TestComplexExperimentRunning.app

        self.request_patcher = patch('gateway_code.server_rest.request')
        self.request = self.request_patcher.start()

        self.idle = _FileUpload(file = open(CURRENT_DIR + 'simple_idle.elf', 'rb'),
                name = 'firmware', filename = 'simple_idle.elf')

        self.echo = _FileUpload(file = open(CURRENT_DIR + 'serial_echo.elf', 'rb'),
                name = 'firmware', filename = 'serial_echo.elf')

        self.profile = _FileUpload(file = open(CURRENT_DIR + 'profile.json', 'rb'),
                name = 'profile', filename = 'profile.json')
        self.reduced_profile = _FileUpload(file = open(CURRENT_DIR + 'reduced_profile.json', 'rb'),
                name = 'profile', filename = 'reduced_profile.json')


        self.files = [self.idle.file, self.echo.file, self.profile.file, self.reduced_profile.file]


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

        # start
        self.request.files = {'firmware': self.idle, 'profile':self.profile}
        ret = self.app.exp_start(123, 'clochette')
        assert ret == {'ret':0}
        time.sleep(5)

        # flash
        self.request.files = {'firmware': self.echo}
        ret = self.app.open_flash()
        assert ret == {'ret':0}

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

