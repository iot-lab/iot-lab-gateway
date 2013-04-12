#! /usr/bin/env python

from gateway_code import server_rest
import multiprocessing
import time

def tests_integration():

    args = ['tests', 'localhost', '8080']
    server_process = multiprocessing.Process(target=server_rest.main, args=[args])
    server_process.start()

    time.sleep(10)

    server_process.terminate()
    server_process.join()





