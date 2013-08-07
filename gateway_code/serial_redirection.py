#! /usr/bin/env python
# -*- coding:utf-8 -*-

"""
Module managing the open node serial redirection
"""

import sys
import time
from subprocess import PIPE
import subprocess
import threading
import atexit
import logging

from gateway_code import config

SOCAT_CMD = ''' socat -d TCP4-LISTEN:20000,reuseaddr open:%s,b%d,echo=0,raw '''
LOGGER = logging.getLogger('gateway_code')


class SerialRedirection(object):
    """
    Class providing node serial redirection to a tcp socket
    """

    def __init__(self, node):
        """
        Init SerialRedirection
        """
        if node not in config.NODES_CFG:
            raise ValueError('Unknown node, not in %r',
                             config.NODES_CFG.keys())
        self.node = node

        self.redirector_thread = None
        self.is_running = False
        self.err = None
        self.out = None

        atexit.register(self.stop)  # cleanup in case of error

    def start(self):
        """
        Start the serial redirection program

        A thread is also run to monitor and reload the program
        """
        if self.is_running:
            return 1

        self.redirector_thread = _SerialRedirectionThread(
            config.NODES_CFG[self.node]['tty'],
            config.NODES_CFG[self.node]['baudrate'])
        self.err = ""
        self.out = ""
        self.is_running = True
        self.redirector_thread.daemon = True
        self.redirector_thread.start()

        return 0

    def stop(self):
        """
        Stop the current serial redirection program
        """
        if not self.is_running:
            return 1

        self.redirector_thread.stop()
        self.redirector_thread.join()

        self.err = self.redirector_thread.err
        self.out = self.redirector_thread.out
        self.is_running = False
        return 0


class _SerialRedirectionThread(threading.Thread):
    """
    Stoppable thread that redirects node serial port to tcp
    """

    def __init__(self, tty, baudrate):

        super(_SerialRedirectionThread, self).__init__()

        self.err = ""
        self.out = ""

        # serial link informations
        self.tty = tty
        self.baudrate = baudrate

        # Stopping thread
        self.stop_thread = False

        # Current process running socat
        self.redirector_process = None

    def run(self):
        """
        Run the thread

        It starts a while loop running a socat command
        """
        import shlex

        cmd_list = shlex.split(SOCAT_CMD % (self.tty, self.baudrate))

        while not self.stop_thread:
            self.redirector_process = subprocess.Popen(
                cmd_list, stdout=PIPE, stderr=PIPE)

            # blocks until socat terminates
            out, err = self.redirector_process.communicate()
            self.out += out
            self.err += err
            retcode = self.redirector_process.returncode
            # On exit, socat gives status:
            #   0 if it terminated due to EOF or inactivity timeout
            #   a positive value on error
            #   a negative value on fatal error.

            # don't print error when 'terminate' causes the error
            if retcode != 0 and (not self.stop_thread):
                LOGGER.error('Open node serial redirection exit: %d', retcode)
                time.sleep(0.5)  # prevent quick loop

    def stop(self):
        """
        Stop the running thread
        """
        self.stop_thread = True

        # kill
        while self.is_alive():
            try:
                if self.redirector_process is not None:
                    self.redirector_process.terminate()
            except OSError as err:
                # errno == 3 'No such proccess'
                # current process is already terminated not an issue
                assert err.errno == 3, 'Unknown error num: %d' % err.errno
                # required instruction if assert disabled
                _ = err.errno
            time.sleep(0.1)

        self.redirector_process = None


def _parse_arguments(args):
    """
    Parsing arguments:

    script.py node
    Only pass arguments to function without script name

    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('node', type=str, choices=config.NODES,
                        help="Node selection")
    arguments = parser.parse_args(args)

    return arguments.node

# direct import of Event to be able to mock it to test main function
# without mocking the 'threading.Event' used in the threading class
from threading import Event


def _main(args):
    """
    Command line main function
    """
    import signal

    node = _parse_arguments(args[1:])
    unlock_main_thread = Event()

    # Create the redirector
    redirect = SerialRedirection(node)
    if redirect.start() != 0:
        print >> sys.stderr, "Could not start redirection"
        exit(1)

    # Wait ctrl+C to stop
    def cb_signal_handler(sig, frame):
        """ Ctrl+C handler """
        print >> sys.stderr, "Got Ctrl+C, Stopping..."
        unlock_main_thread.set()
    signal.signal(signal.SIGINT, cb_signal_handler)
    print 'Press Ctrl+C to stop the application'
    unlock_main_thread.wait()

    redirect.stop()
    print >> sys.stderr, 'Stopped.'
    print >> sys.stderr, ''
    print >> sys.stderr, 'Out log:'
    print >> sys.stderr, redirect.out,
    print >> sys.stderr, ''
    print >> sys.stderr, 'Error log:'
    print >> sys.stderr, redirect.err,
