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


""" Module managing an external background process """

import os
import time
import subprocess
import signal
import threading
import atexit

import logging
LOGGER = logging.getLogger('gateway_code')


class ExternalProcess(threading.Thread):
    # pylint: disable=no-member,method-hidden
    """ Class running an external process in background

    It's implemented as a stoppable thread running the process in a loop.
    """

    stdout = None

    def __init__(self):  # pylint:disable=super-init-not-called
        self._thread_init()  # threading.Thread init and set daemon
        self._started = threading.Event()
        self.process = None
        if self.stdout is None:
            self.stdout = open(os.devnull, 'w')

        # Thread management
        self._run = False

        atexit.register(self.stop)  # cleanup in case of error

    def _thread_init(self):
        """ Init Thread.
        Must be called in __init__ and after stop.
        This will allow calling start-stop without re-instanciating """
        # threading.Thread init
        super(ExternalProcess, self).__init__(target=self._target)
        self.daemon = True

    def start(self):
        """ Start the external process Thread """
        self._run = True
        LOGGER.debug('%s start', self.NAME)
        super(ExternalProcess, self).start()
        # wait for 'Popen' to have been called
        return 0 if self._started.wait(15.0) else 1

    def stop(self):
        """ Stop the running thread """
        self._run = False
        LOGGER.debug('%s stop', self.NAME)
        signals = self.signals_iter()

        # kill
        while self.is_alive():
            try:
                if self.process is not None:
                    sig = next(signals)
                    self.process.send_signal(sig)
            except OSError as err:
                # errno == 3 'No such proccess', already terminated: OK
                assert err.errno == 3, 'Unknown error num: %r' % err.errno
            time.sleep(0.1)
        self.process = None
        self._started.clear()
        LOGGER.debug('%s stopped', self.NAME)

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
        for _ in range(sigterm):
            yield signal.SIGTERM

        LOGGER.info('External process signal: escalading to SIGINT')
        for _ in range(sigint):
            yield signal.SIGINT

        LOGGER.warning('External process signal: escalading to SIGKILL')
        while True:
            yield signal.SIGKILL

    def _target(self):
        """ Starts a while loop running a socat command """
        LOGGER.debug('%s thread started', self.NAME)

        while self._run:
            self._call_process(self.stdout)

    def _call_process(self, out):
        """ Call 'process_cmd' and wait until it finishes
        'self.proc' is updated with the current socat process
        Logs an error if it terminates with a non-null return value """
        self.process = subprocess.Popen(self.process_cmd,
                                        stdout=out, stderr=out)
        # 'start' can now exit
        self._started.set()

        # blocks until the process terminates
        retcode = self.process.wait()
        # On exit, the process gives its status:
        #   0 if it terminated due to EOF or inactivity timeout
        #   a positive value on error
        #   a negative value on fatal error.

        # don't print error when 'terminate' causes the error

        ret = self.check_error(retcode)
        time.sleep(0.5)  # prevent quick loop
        self._started.clear()
        return ret
