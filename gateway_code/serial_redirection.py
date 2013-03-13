#! /usr/bin/env python
# -*- coding:utf-8 -*-


"""
serial_redirection script
"""

import sys
from subprocess import PIPE
import subprocess
import shlex
import threading
import time
import signal



# import common configuration
from gateway_code import config



def _num_arguments_required(func):
    """
    Returns the number of arguments required to call 'func'

    Based on the function signature
    Method which have n arguments required 'n-1' arguments to be called
        as self is allready provided

    Accepts only methods or functions

    """
    from inspect import getargspec, ismethod, isfunction
    # manage only functions and methods
    if not (ismethod(func) or isfunction(func)):
        raise ValueError, 'Required method or function'

    num = len(getargspec(func)[0])

    # 'self' first argument is allready provided
    if ismethod(func):
        num -= 1

    return num



class SerialRedirection():
    """
    Class providing node serial redirection to a tcp socket
    Using a  start, stop, error_handler interface
    """

    def __init__(self, node,
            error_handler = None, handler_arg = None):

        """
        error_handler signature:
            def error_handler(handler_arg, error_tuple)
        error_tuple = (error_num, error_str)

        """
        if node not in config.NODES_CFG:
            raise ValueError, 'Unknown node, not in %r' \
                    % config.NODES_CFG.keys()
        self.node = node

        # check handler signature
        if error_handler is not None:
            if _num_arguments_required(error_handler) != 2:
                raise ValueError, 'Error handler should accept two arguments'


        self.redirector_thread = _SerialRedirectionThread(\
                config.NODES_CFG[self.node]['tty'],\
                config.NODES_CFG[self.node]['baudrate'], \
                self.__cb_error_handler)

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

    def __cb_error_handler(self, error_str):
        """
        Error callback which calls caller error_handler with arguments
        """
        self.err = self.redirector_thread.err
        self.out = self.redirector_thread.out

        if self.error_handler is not None:
            self.error_handler(self.handler_arg, error_str)

class _SerialRedirectionThread(threading.Thread):
    """
    Stoppable thread that redirects node serial port to tcp

    It calls 'error_handler' on error.
    """


    def __init__(self, tty, baudrate, error_handler):


        super(_SerialRedirectionThread, self).__init__()

        self.err = ""
        self.out = ""

        # serial link informations
        self.node = {'tty': tty, 'baudrate': baudrate}

        # Handler called on error on socat
        if error_handler is not None:
            if _num_arguments_required(error_handler) != 1:
                raise ValueError, 'Error handler should accept one argument'
        self.error_handler = error_handler

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

        cmd = '''echo "Not Implemented"'''
        cmd_list = shlex.split(cmd)

        # Run openocd

        while not self.stop_thread:
            # Pre-run tests (and repeated errors handling maybe)
            # test_error = False
            # if test_error:
            #     error_str = ""
            #     if self.error_handler is not None:
            #         self.error_handler(error_str)
            #     break

            self.redirector_process = subprocess.Popen(\
                    cmd_list, stdout=PIPE, stderr=PIPE)
            out, err = self.redirector_process.communicate()
            self.out += out
            self.err += err
            retcode = self.redirector_process.returncode

            if retcode != 0:
                error_str = "Process returned non zero code %d" % retcode
                if self.error_handler is not None:
                    self.error_handler(error_str)
                break

        self.is_running = False



    def stop(self):
        """
        Stop the running thread
        """

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
            time.sleep(0.1)

        self.redirector_process = None




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
    arguments = parser.parse_args(args)

    return arguments.node, arguments.baudrate





def main(args):
    """
    Command line main function
    """
    import mutex

    def __main_error_handler(arg, err):
        """
        Error handler in command line
        """
        error_num, error_str = err
        print >> sys.stderr, "main_error_handler"
        print >> sys.stderr, "arg: %r" % arg
        print >> sys.stderr, "error: ('%d','%s')" % (error_num, error_str)
        exit(error_num)

    # main blocking mutex
    main_mutex = mutex.mutex()
    main_mutex.lock(None, None)
    def cb_signal_handler(sig, frame):
        """
        Ctrl+C handler
        """
        print >> sys.stderr, 'Got Ctrl+C, Stopping...'
        main_mutex.unlock()


    node = parse_arguments(args)
    thread = SerialRedirection(node, __main_error_handler)

    # Wait ctrl+C to stop
    print 'Press Ctrl+C to stop the application'
    signal.signal(signal.SIGINT, cb_signal_handler)
    # test this shit
    assert 0 # not tested regarding arguments number
    main_mutex.lock(thread.stop, None)
    print >> sys.stderr, 'Stopped.'


if __name__ == '__main__':
    main(sys.argv)

