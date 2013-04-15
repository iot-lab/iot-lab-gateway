#! /usr/bin/env python

from gateway_code import server_rest
import multiprocessing
import time

URL="http://localhost:8080/"

import requests
def req_method(url, method='GET', data=None):

    method_url = URL + url

    if (method == 'POST'):
        headers = {'content-type': 'application/json'}
        r = requests.post(method_url, data=data, headers=headers)
    elif (method == 'MULTIPART'):
        r = requests.post(method_url, files=data)
    elif (method == 'DELETE'):
        r = requests.delete(method_url)
    elif (method = 'PUT')
        r = requests.put(method_url)
    else:
        r = requests.get(method_url)

    if (r.status_code == requests.codes.ok):
        return r.text
    else:
        # we have HTTP error (code != 200)
        print("HTTP error code : %s \n%s" % (r.status_code, r.text))



def start_exp(id = 123, user = 'clochette'):
    with open('simple_idle.elf', 'rb') as firmware:
        with open('profile.json', 'rb') as profile:
            files = {'firmware': firmware, 'profile':profile}
            req_method('/exp/start/%d/%s' % (id, user), 'MULTIPART', data=files)

def stop_exp():
    req_method('/exp/stop', 'DELETE')


def flash_firmware():
    with open('serial_echo.elf', 'rb') as firmware:
        files = {'firmware': firmware}
        req_method('/open/flash', 'MULTIPART', data=files)

def reset_open():
    req_method('/open/reset', 'PUT')




#files = {'file': open('report.xls', 'rb')}

import unittest

class TestComplexExperimentRunning(unittest.TestCase):

    @classmethod
    def setUpClass():
        args = ['tests', 'localhost', '8080']
        self.server_process = multiprocessing.Process(target=server_rest.main, args=[args])
        self.server_process.start()

    @classmethod
    def tearDownClass():
        self.server_process.terminate()
        self.server_process.join()

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
        stop_exp()




