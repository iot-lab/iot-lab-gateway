#! /usr/bin/env python
# -*- coding:utf-8 -*-

""" Module managing the open node serial redirection """

import sys
import os
import time
import subprocess
import threading
import atexit
import logging
import shlex

# direct import of Event to be able to mock it to test main function
# without mocking the 'threading.Event' used in the threading class
from threading import Event

SOCAT = 'socat -d TCP4-LISTEN:20000,reuseaddr open:{tty},b{baud},echo=0,raw'
LOGGER = logging.getLogger('gateway_code')


class SerialRedirection(object):
    """ Class providing node serial redirection to a tcp socket """

    def __init__(self, tty, baudrate):
        """
        Init SerialRedirection
        """
        self.tty = tty
        self.baudrate = baudrate

        self.redirector_thread = None
        self.is_running = False

        atexit.register(self.stop)  # cleanup in case of error

    def start(self):
        """
        Start the serial redirection program

        A thread is also run to monitor and reload the program
        """
        if self.is_running:
            return 1

        self.redirector_thread = _SerialRedirectionThread(
            self.tty, self.baudrate)
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

        self.is_running = False
        return 0


class _SerialRedirectionThread(threading.Thread):
    """
    Stoppable thread that redirects node serial port to tcp
    """

    def __init__(self, tty, baudrate):
        # threading.Thread init
        super(_SerialRedirectionThread, self).__init__()

        self.tty = tty
        self.baudrate = baudrate
        self.proc = None  # Socat process

        # Thread management
        self.stop_thread = False

    def run(self):
        """ Starts a while loop running a socat command """

        socat_cmd = shlex.split(SOCAT.format(tty=self.tty, baud=self.baudrate))

        with open(os.devnull, 'w') as fnull:
            while not self.stop_thread:
                self._call(socat_cmd, fnull)

    def _call(self, socat_cmd, out):
        """ Call 'socat_cmd' and wait until it finishes
        'self.proc' is updated with the current socat process
        Logs an error if it terminates with a non-null return value """
        self.proc = subprocess.Popen(socat_cmd, stdout=out, stderr=out)

        # blocks until socat terminates
        retcode = self.proc.wait()
        # On exit, socat gives status:
        #   0 if it terminated due to EOF or inactivity timeout
        #   a positive value on error
        #   a negative value on fatal error.

        # don't print error when 'terminate' causes the error
        if retcode and (not self.stop_thread):
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
                self.proc.terminate()
            except AttributeError:
                pass  # proc is None
            except OSError as err:
                # errno == 3 'No such proccess'
                # current process is already terminated not an issue
                assert err.errno == 3, 'Unknown error num: %d' % err.errno
            time.sleep(0.1)

        self.proc = None


def _parse_arguments(args):
    """
    Parsing arguments:

    script.py <tty> <baudrate>
    Only pass arguments to function without script name

    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('tty', type=str, help="Serial device")
    parser.add_argument('baudrate', type=int, help="Serial baudrate")
    opts = parser.parse_args(args)

    return opts


def _main(args):
    """
    Command line main function
    """
    import signal

    opts = _parse_arguments(args[1:])
    unlock_main_thread = Event()

    # Create the redirector
    redirect = SerialRedirection(opts.tty, opts.baudrate)
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
