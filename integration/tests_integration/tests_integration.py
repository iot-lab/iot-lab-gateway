#! /usr/bin/env python

from gateway_code import server_rest
import multiprocessing
import time
import os


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) + '/'
URL = "http://localhost:8080/"

import requests
def req_method(url, method='GET', data=None):

    method_url = URL + url

    if (method == 'POST'):
        headers = {'content-type': 'application/json'}
        req = requests.post(method_url, data=data, headers=headers)
    elif (method == 'MULTIPART'):
        req = requests.post(method_url, files=data)
    elif (method == 'DELETE'):
        req = requests.delete(method_url)
    elif (method == 'PUT'):
        req = requests.put(method_url)
    else:
        req = requests.get(method_url)

    if (req.status_code == requests.codes.ok):
        return req.text
    else:
        # we have HTTP error (code != 200)
        print("HTTP error code : %s \n%s" % (req.status_code, req.text))



def start_exp(exp_id = 123, user = 'clochette'):
    with open(CURRENT_DIR + 'simple_idle.elf', 'rb') as firmware:
        with open(CURRENT_DIR + 'profile.json', 'rb') as profile:
            files = {'firmware': firmware, 'profile':profile}
            req_method('/exp/start/%d/%s' % (exp_id, user), 'MULTIPART', data=files)

def stop_exp():
    req_method('/exp/stop', 'DELETE')


def flash_firmware():
    with open(CURRENT_DIR + 'serial_echo.elf', 'rb') as firmware:
        files = {'firmware': firmware}
        req_method('/open/flash', 'MULTIPART', data=files)

def reset_open():
    req_method('/open/reset', 'PUT')




#files = {'file': open('report.xls', 'rb')}

import unittest

class TestComplexExperimentRunning(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        args = ['tests', 'localhost', '8080']
        cls.server_process = multiprocessing.Process(\
                target=server_rest.main, args=[args])
        cls.server_process.start()

        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls.server_process.terminate()
        cls.server_process.join()

    def a_tests_integration(self):
        """
        Start exp(idle)
        Stop experiment
        """

        start_exp()
        stop_exp()

    def b_tests_integration(self):
        start_exp()
        flash_firmware()
        reset_open()
        stop_exp()




