# -*- coding:utf-8 -*-

# This file is a part of IoT-LAB gateway_code
# Copyright (C) 2015 INRIA (Contact: admin@iot-lab.info)
# Contributor(s) : see AUTHORS file
#
# This software is governed by the CeCILL license under French law
# and abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# http://www.cecill.info.
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.


""" Module managing the open node serial redirection """

import os
import time
import subprocess
import signal
import shlex
import threading
import atexit

import logging
LOGGER = logging.getLogger('gateway_code')


class SerialRedirection(threading.Thread):
    """ Class providing node serial redirection to a tcp socket

    It's implemented as a stoppable thread running socat in a loop.

    Socat is run in a loop instead of using 'tcp-listen,..,fork' because we
    want
    """
    SOCAT = ('socat -d'
             ' TCP4-LISTEN:20000,reuseaddr'
             ' open:{tty},b{baud},echo=0,raw')
    DEVNULL = open(os.devnull, 'w')

    def __init__(self, tty, baudrate):  # pylint:disable=super-init-not-called
        self._thread_init()  # threading.Thread init and set daemon
        self.tty = tty
        self._started = threading.Event()
        self.socat_cmd = shlex.split(self.SOCAT.format(tty=tty, baud=baudrate))
        self.redirector = None

        # Thread management
        self._run = False

        atexit.register(self.stop)  # cleanup in case of error

    def _thread_init(self):
        """ Init Thread.
        Must be called in __init__ and after stop.
        This will allow calling start-stop without re-instanciating """
        # threading.Thread init
        super(SerialRedirection, self).__init__(target=self._target)
        self.daemon = True

    def start(self):
        """ Start the serial redirection Thread """
        self._run = True
        LOGGER.debug('SerialRedirection start')
        super(SerialRedirection, self).start()
        # wait for 'Popen' to have been called
        return 0 if self._started.wait(15.0) else 1

    def stop(self):
        """ Stop the running thread """
        self._run = False
        LOGGER.debug('SerialRedirection stop')
        signals = self.signals_iter()

        # kill
        while self.is_alive():
            try:
                sig = signals.next()
                self.redirector.send_signal(sig)
            except OSError as err:
                # errno == 3 'No such proccess', already terminated: OK
                assert err.errno == 3, 'Unknown error num: %r' % err.errno
            time.sleep(0.1)
        self.redirector = None
        self._started.clear()
        LOGGER.debug('SerialRedirection stoped')

        # Re-init thread to allow calling 'start' once again
        self._thread_init()
        return 0

    @staticmethod
    def signals_iter(sigterm=10, sigint=10):
        """Generator to incrementally send more important signals.

        Yields:

        * SIGTERM `sigterm` times
        * then SIGINT `sigint` times
        * then SIGKILL indefinitely

        Signals information:
          ftp://ftp.gnu.org/old-gnu/Manuals/glibc-2.2.3/html_chapter/libc_24.html#SEC472
          # pylint:disable=line-too-long  # noqa
        """
        sigterm = int(sigterm)
        sigint = int(sigint)
        for _ in xrange(0, sigterm):
            yield signal.SIGTERM

        LOGGER.info('SerialRedirection signal: escalading to SIGINT')
        for _ in xrange(0, sigint):
            yield signal.SIGINT

        LOGGER.warning('SerialRedirection signal: escalading to SIGKILL')
        while True:
            yield signal.SIGKILL

    def _target(self):
        """ Starts a while loop running a socat command """
        LOGGER.debug('SerialRedirection thread started')

        while self._run:
            self._call_socat(self.DEVNULL)

    def _call_socat(self, out):
        """ Call 'socat_cmd' and wait until it finishes
        'self.proc' is updated with the current socat process
        Logs an error if it terminates with a non-null return value """
        self.redirector = subprocess.Popen(self.socat_cmd,
                                           stdout=out, stderr=out)
        # 'start' can now exit
        self._started.set()

        # blocks until socat terminates
        retcode = self.redirector.wait()
        # On exit, socat gives status:
        #   0 if it terminated due to EOF or inactivity timeout
        #   a positive value on error
        #   a negative value on fatal error.

        # don't print error when 'terminate' causes the error

        if retcode and self._run:
            LOGGER.error('SerialRedirection exit: %d', retcode)
            if not os.path.exists(self.tty):
                LOGGER.warning('%s not found', self.tty)
            time.sleep(0.5)  # prevent quick loop
        return retcode
