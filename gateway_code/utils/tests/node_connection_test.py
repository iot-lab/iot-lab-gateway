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


""" Test node_connection.OpenNodeConnection """

import time
import unittest
import threading
from subprocess import Popen, PIPE

import mock

from ..node_connection import OpenNodeConnection

# pylint:disable=missing-docstring


class TestOpenNodeConnection(unittest.TestCase):
    """ Test the open node autotest interface

    Run tests with socat to be close to serial_redirection """

    def setUp(self):
        port = OpenNodeConnection.PORT
        tcp_listen = 'tcp4-listen:{port},reuseaddr,fork'.format(port=port)
        cmd = ['socat', '-', tcp_listen]
        self.redirect = Popen(cmd, stdout=PIPE, stdin=PIPE)

        self.on_thread = threading.Thread(target=self._open_node_thread)
        self.on_thread.start()
        self.write_delay = 0

    def tearDown(self):
        self.redirect.terminate()
        self.on_thread.join()

    def _open_node_thread(self):
        try:
            while True:
                line = self.redirect.stdout.readline()
                if not line:
                    break
                time.sleep(self.write_delay)
                self.redirect.stdin.write('READ_LINE %s' % line)
        except (AttributeError, IOError) as err:
            print err
        else:
            print "_open_node_thread stopped"

    def test_sending_multiple_commands(self):
        with OpenNodeConnection() as conn:

            cmd = ['cmd']
            ret = conn.send_command(cmd)
            self.assertEquals(['READ_LINE'] + cmd, ret)

            cmd = ['command', 'arg1', 'arg2']
            ret = conn.send_command(cmd)
            self.assertEquals(['READ_LINE'] + cmd, ret)

            cmd = ['command3', 'arg1', 'arg2', 'arg3', 'arg4']
            ret = conn.send_command(cmd)
            self.assertEquals(['READ_LINE'] + cmd, ret)

    def test_sending_with_delay(self):
        with OpenNodeConnection() as conn:

            self.write_delay = 1
            ret = conn.send_command(['cmd'])
            self.assertEquals(['READ_LINE', 'cmd'], ret)

            self.write_delay = 2
            ret = conn.send_command(['cmd'])
            self.assertEquals(['READ_LINE', 'cmd'], ret)

            self.write_delay = 3
            ret = conn.send_command(['cmd'])
            self.assertEquals(['READ_LINE', 'cmd'], ret)

            self.write_delay = 4
            ret = conn.send_command(['cmd'])
            self.assertEquals(['READ_LINE', 'cmd'], ret)

    def test_sending_one_command(self):
        cmd = ['cmd']
        ret = OpenNodeConnection.send_one_command(cmd)
        self.assertEquals(['READ_LINE'] + cmd, ret)

        cmd = ['command', 'arg1', 'arg2']
        ret = OpenNodeConnection.send_one_command(cmd)
        self.assertEquals(['READ_LINE'] + cmd, ret)

        cmd = ['command3', 'arg1', 'arg2', 'arg3', 'arg4']
        ret = OpenNodeConnection.send_one_command(cmd)
        self.assertEquals(['READ_LINE'] + cmd, ret)

    def test_no_answer(self):
        # Disable node answers
        self.redirect.stdin = mock.Mock()

        ret = OpenNodeConnection.send_one_command(['cmd'], timeout=0.1)
        self.assertEquals(None, ret)

    def test_timeout(self):
        self.write_delay = 0.2
        ret = OpenNodeConnection.send_one_command(['cmd'], timeout=0.1)
        self.assertEquals(None, ret)


class TestOpenNodeConnectionErrors(unittest.TestCase):

    def test_connection_error(self):
        self.assertRaises(IOError, OpenNodeConnection.try_connect,
                          ('localhost', 20000), tries=2, step=0.1)

    def test_context_manager_error(self):
        with self.assertRaises(RuntimeError):
            with OpenNodeConnection():
                self.fail('Should not have entered context manager')
