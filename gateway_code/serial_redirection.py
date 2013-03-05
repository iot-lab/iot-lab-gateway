#! /usr/bin/env python
# -*- coding:utf-8 -*-


"""
serial_redirection script
"""

import sys
from subprocess import Popen, PIPE
import shlex
import threading
import time
import signal
import inspect



# import common configuration
import config


class _SerialRedirectionThread(threading.Thread):

    def __init__(self, tty, baudrate, error_handler, handler_arg):


        super(_SerialRedirectionThread, self).__init__()

        self.err = ""
        self.out = ""

        # serial link informations
        self.tty = tty
        self.baudrate = baudrate

        # Handler called on error on socat
        self.error_handler = error_handler
        self.handler_arg = handler_arg

        # Stopping thread
        self.stop_thread = False
        self.is_running = False

        # Current process running socat
        self.redirector_process = None

    def start(self):
        """
        Start a new thread
        """

        self.is_running = True

        super(_SerialRedirectionThread, self).start()

    def run(self):
        """
        Run the thread

        It starts a while loop running a socat command
        """

        cmd = '''echo "test"'''
        cmd_list = shlex.split(cmd)

        # Run openocd

        while not self.stop_thread:
            # Pre-run tests (and repeated errors handling maybe)
            test_error = False
            if test_error:
                error_str = ""
                if self.error_handler is not None:
                    self.error_handler(self.handler_arg, error_str)
                break

            self.redirector_process = Popen(cmd_list, stdout=PIPE, stderr=PIPE)
            out, err = self.redirector_process.communicate()
            self.out += out
            self.err += err

            if self.redirector_process.returncode != 0:
                time.sleep(0.2)

            # debug
            time.sleep(0.2)

        self.is_running = False



    def stop(self):

        self.stop_thread = True

        # kill
        while self.is_running:
            try:
                self.redirector_process.terminate()
            except OSError, err:
                if err.errno == 3:
                    # 'No such proccess'
                    # It means that the current process is already terminated
                    pass
                else:
                    raise err
            time.sleep(1)

        self.redirector_process = None


class SerialRedirection():

    def __init__(self, tty, baudrate = 500000, \
            error_handler = None, handler_arg = None):
        """

        error_handler signature:
            def error_handler(handler_arg, error_string)
        """

        # check handler signature
        if error_handler is not None:
            if len(inspect.getargspec(error_handler)[0]) != 2:
                raise ValueError, 'Error handler should accept two arguments'


        self.redirector_thread = _SerialRedirectionThread(\
                tty, baudrate, self.__error_handler, self)
        self.error_handler = error_handler
        self.handler_arg = handler_arg
        self.is_running = False
        self.err = None
        self.out = None


    def start(self):
        """
        Start a new SerialRedirection
        """

        if self.is_running:
            # Already running
            return 1

        self.err = ""
        self.out = ""

        self.is_running = True
        self.redirector_thread.start()

        return 0


    def stop(self):
        """
        Stop the current Serial Redirection
        """

        if not self.is_running:
            # not running
            return 1

        self.redirector_thread.stop()
        self.redirector_thread.join()
        self.is_running = False

        self.err = self.redirector_thread.err
        self.out = self.redirector_thread.out


        # logging ?
        return 0

    def __error_handler(self, error_str):
        self.err = self.redirector_thread.err
        self.out = self.redirector_thread.out

        if self.error_handler is not None:
            self.error_handler(self.handler_arg, error_str)


def parse_arguments(args):
    """
    Parsing arguments:

    script.py node firmware.elf
    Only pass arguments to function without script name

    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('node', type=str, choices=config.NODES,
            help="Node selection")
    parser.add_argument('baudrate', type=int, default=500000, \
            help="baudrate, default from config")
    arguments = parser.parse_args(args)

    return arguments.node, arguments.baudrate



def error_handler_test(arg, error_str):
    print "error_handler_test"
    print arg
    print error_str

if __name__ == '__main__':


    NODE, BAUDRATE = parse_arguments(sys.argv[1:])

    if BAUDRATE is None:
        BAUDRATE = config.NODES_CFG[NODE]['baudrate']

    TTY = config.NODES_CFG[NODE]['tty']





#    def __init__(self, tty, baudrate = 500000, 
#           error_handler = None, handler_arg = None):

    THREAD = SerialRedirection(TTY, BAUDRATE, error_handler_test)

    def cb_signal_handler(sig, frame):
        print >> sys.stderr, 'Got Ctrl+C'
        THREAD.stop()

    signal.signal(signal.SIGINT, cb_signal_handler)

    print 'start'
    THREAD.start()
    print 'started'
    time.sleep(10)
    print 'Stop'
    THREAD.stop()
    print 'stopped'

    print "Err:"
    print THREAD.err
    print "Out:"
    print THREAD.out
    print 'done'

