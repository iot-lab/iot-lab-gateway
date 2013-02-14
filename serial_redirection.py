#! /usr/bin/env python
# -*- coding:utf-8 -*-


"""
serial_redirection script
"""

import argparse
import sys
from subprocess import Popen, PIPE
import shlex
import threading
import time
import signal



# import common configuration
import config


class __SerialRedirectionThread(threading.Thread):

    def __init__(self, tty, baudrate = 500000, error_handler = None, handler_arg = None):


        #print super(__SerialRedirectionThread, self)
        #super(__SerialRedirectionThread, self).__init__()
        threading.Thread.__init__(self)

        self.err = ""
        self.out = ""

        # serial link informations
        self.tty = tty
        self.baudrate = baudrate

        # Handler called on error on socat
        self.error_handler = None
        self.handler_arg = None

        # Stopping thread
        self.stop_thread = False
        self.is_running = False

        # Current process running socat
        self.current_redirector_process = None

    def start(self):
        self.is_running = True
        #super(__SerialRedirectionThread, self).start()

        threading.Thread.start(self)

    def run(self):
        print 'Run'

        cmd = '''echo "test"'''
        cmd_list = shlex.split(cmd)

        # Run openocd

        while not self.stop_thread:
            self.current_redirector_process = Popen(cmd_list, stdout=PIPE, stderr=PIPE)
            time.sleep(0.2)
            #self.current_redirector_process.wait()
            out, err = self.current_redirector_process.communicate()

            self.out += out
            self.err += err

        self.is_running = False

    def stop(self):

        self.stop_thread = True

        # kill
        while self.is_running:
            self.current_redirector_process.terminate()
            time.sleep(1)

        self.current_redirector_process = None


# class SerialRedirection():
#
#
#     def run(self, error_handler, handler_arg):
#         """
#         error_handler == method with 1 argument or none
#         """
#
#         self.is_running = True
#         self.error_handler = error_handler
#         self.handler_arg = handler_arg
#
#         self.redirector_thread = threading.Thread(target=self.run)
#         self.redirector_thread.start()
#
#
#     def stop(self):
#
#
#         self.is_running = False
#
#         self.error_handler = None
#         self.handler_arg = None
#
#         # kill the current Popen
#         # join thread
#         self.redirector_thread = None
#
#
#
#         # logging ?
#
#
#
#     def run(self, ttyelf_file):
#         cmd_list = shlex.split(cmd)
#
#         # Run openocd
#         openocd = Popen(cmd_list, stdout=PIPE, stderr=PIPE)
#         out, err = openocd.communicate() # nothing is written to stdout
#         ret = openocd.returncode
#
#         self.out = out
#         self.err = err
#
#         # Check execution
#         if ret != 0:
#             # logging ???
#             pass
#
#         return ret
#
#     def stop(self):
#         pass
#


def parse_arguments(args):
    """
    Parsing arguments:

    script.py node firmware.elf
    Only pass arguments to function without script name

    """
    parser = argparse.ArgumentParser()
    parser.add_argument('node', type=str, choices=config.NODES,
            help="Node selection")
    parser.add_argument('baudrate', type=int, default=500000,\
            help="baudrate, default from config")
    arguments = parser.parse_args(args)

    return arguments.node, arguments.baudrate



if __name__ == '__main__':


    NODE, BAUDRATE = parse_arguments(sys.argv[1:])

    if BAUDRATE is None:
        BAUDRATE = config.NODES_CFG[NODE]['baudrate']



    THREAD = __SerialRedirectionThread("LALA")

    def signal_handler(signal, frame):
        print >> sys.stderr, 'Got Ctrl+C'
        THREAD.stop()

    signal.signal(signal.SIGINT, signal_handler)

    print 'start'
    THREAD.start()
    print 'started'
    time.sleep(10)
    print 'Stop'
    THREAD.stop()
    print 'stopped'
    THREAD.join()

    print "Err:"
    print THREAD.err
    print "Out:"
    print THREAD.out
    print 'done'

