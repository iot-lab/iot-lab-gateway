# -*- coding: utf-8 -*-

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


""" Open node communication interface.

Connects to the serial_redirection tcp socket and allow sending commands """

import time
import socket

import logging
LOGGER = logging.getLogger('gateway_code')


class OpenNodeConnection(object):
    """ Connects to serial port redirection and sends messages """
    HOST = 'localhost'
    PORT = 20000

    def __init__(self, host=HOST, port=PORT, timeout=5.0):
        self.address = (host, port)
        self.timeout = timeout
        self.fd = None  # pylint:disable=invalid-name

    def start(self):
        """ Connect to the serial_redirection """
        try:
            sock = self.try_connect(self.address)
            sock.settimeout(self.timeout)  # pylint:disable=no-member
            self.fd = sock.makefile('rw')
            return 0
        except IOError:
            return 1

    def stop(self):
        """ Close the connection and wait until the connection is ready
        for reconnection """
        self.fd.close()
        self.fd = None

        # Wait redirection restarted
        # Should not wait on start because connection should work instantly
        # As it's the real user use case
        time.sleep(1.0)
        return 0

    @staticmethod
    def try_connect(address=(HOST, PORT), tries=10, step=0.5):
        """ Try connecting 'tries' time to address (host, port) tuple
        Sleep 'step' between each tries.
        If last trial fails, the IOError is raised

        The goal is to be resilient to the fact that serial_aggregator might be
        (re)starting.  """
        # Run 'tries -1' times with 'try except'
        for _ in range(0, tries - 1):
            try:
                return socket.create_connection(address)
            except IOError:
                time.sleep(step)

        # Last connection should run an exception
        return socket.create_connection(address)

    def send_command(self, command_list):
        """ Send command and wait for answer """
        assert isinstance(command_list, (list, tuple))
        packet = ' '.join(command_list)

        LOGGER.debug("Command send:   %r", packet)
        self._writeline(packet)
        answer = self._readline()
        LOGGER.debug("Command answer: %r", answer)
        return answer

    def empty(self):
        """ Empty out buffer """
        while self._readline() is not None:
            pass

    def _writeline(self, line):
        """ Write a line """
        self.fd.write(line + '\n')
        self.fd.flush()

    def _readline(self):
        """ Read a line """
        try:
            answer = self.fd.readline()
            if answer.endswith('\n'):
                return answer.strip().split(' ')
        except (socket.timeout, IOError) as err:
            LOGGER.warning("Read timeout: %s", err)
        return None

    @classmethod
    def send_one_command(cls, command_list, *args, **kwargs):
        """ Quick sending function.
        Connects, sends, reads answer and disconnects """
        with cls(*args, **kwargs) as conn:
            return conn.send_command(command_list)

    def __enter__(self):
        ret = self.start()
        if ret:
            raise RuntimeError("Error when starting serial, see logger")
        return self

    def __exit__(self, _type, _value, _traceback):
        self.stop()
