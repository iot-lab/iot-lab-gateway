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


""" test serial_redirection module """

import os
import time
import logging
import socket
from subprocess import Popen, PIPE
import unittest

import mock

from gateway_code.common import wait_tty
from ..serial_redirection import SerialRedirection
from ..node_connection import OpenNodeConnection

# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint <= 1.3
# pylint: disable=too-many-public-methods
# pylint >= 1.4
# pylint: disable=too-few-public-methods
# pylint: disable=no-member

CURRENT_DIR = os.path.dirname(__file__)


class _SerialRedirectionTestCase(unittest.TestCase):
    """ SerialRedirection class test """

    def setUp(self):
        self.tty = '/tmp/ttySRT'
        self.baud = 500000
        self.redirect = None

        self.serial = self._serial(self.tty, self.baud)
        wait_tty(self.tty, mock.Mock(side_effect=RuntimeError()), 5)

    def tearDown(self):
        self.serial.terminate()
        self.serial.kill()
        self.redirect.stop()

    @staticmethod
    def _serial(tty, baud):
        """Create a local pty with socat."""
        cmd = ['socat', '-', 'pty,link=%s,raw,b%d,echo=0' % (tty, baud)]
        return Popen(cmd, stdout=PIPE, stdin=PIPE)


class TestSerialRedirection(_SerialRedirectionTestCase):
    """Test regular SerialRedirection."""

    def test_serialredirection_execution(self):
        """ Test a standard SerialRedirection execution """
        self.redirect = SerialRedirection(self.tty, self.baud)
        self.redirect.start()

        for i in range(0, 3):
            # connect to port 20000
            conn = OpenNodeConnection.try_connect(('0.0.0.0', 20000))

            # TCP send
            sock_txt = 'HelloFromSock: %u\n' % i
            conn.send(sock_txt)
            ret = self.serial.stdout.read(len(sock_txt))
            self.assertEquals(ret, sock_txt)
            logging.debug(ret)

            # Serial send
            serial_txt = 'HelloFromSerial %u\n' % i
            self.serial.stdin.write(serial_txt)
            ret = conn.recv(len(serial_txt))
            self.assertEquals(ret, serial_txt)
            logging.debug(ret)

            conn.close()

        self.redirect.stop()

    def test_serialredirection_multiple_uses(self):
        """ Test calling multiple times start-stop """
        self.redirect = SerialRedirection(self.tty, self.baud)
        self.assertEquals(0, self.redirect.start())
        self.assertEquals(0, self.redirect.stop())
        self.assertEquals(0, self.redirect.start())
        self.assertEquals(0, self.redirect.stop())
        self.assertEquals(0, self.redirect.start())
        self.assertEquals(0, self.redirect.stop())

    def test_serialredirection_exclusion(self):
        """ Check the exclusion of multiple connection on SerialRedirection """
        self.redirect = SerialRedirection(self.tty, self.baud)
        self.redirect.start()

        conn = OpenNodeConnection.try_connect(('0.0.0.0', 20000))
        time.sleep(1)
        # Second connection should fail
        self.assertRaises(IOError,
                          socket.create_connection, ('0.0.0.0', 20000))
        conn.close()
        self.redirect.stop()
