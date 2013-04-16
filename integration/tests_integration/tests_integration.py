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

        self.files = [self.idle.file, self.echo.file, self.profile.file]




    def tearDown(self):
        self.request.stop()
        for file_obj in self.files:
            file_obj.close()

    def a_tests_integration(self):
        """
        Start exp(idle)
        Stop experiment
        """
        self.request.files = {'firmware': self.idle, 'profile':self.profile}

        print >> sys.stderr, self.app.exp_start(123, 'clochette')
        print >> sys.stderr, self.app.exp_stop()


    def b_tests_integration(self):
        return

        self.request.files = {'firmware': self.idle, 'profile':self.profile}
        print >> sys.stderr, self.app.exp_start(123, 'clochette')

        self.request.files = {'firmware': self.echo}
        print >> sys.stderr, self.app.open_flash()
        print >> sys.stderr, self.reset_open()

        print >> sys.stderr, self.app.exp_stop()




