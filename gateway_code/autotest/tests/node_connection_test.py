# -*- coding: utf-8 -*-

""" Test node_connection.OpenNodeConnection """

import mock
import unittest
import threading
from subprocess import Popen, PIPE

from gateway_code.autotest import node_connection

# pylint:disable=missing-docstring


class TestOpenNodeConnection(unittest.TestCase):
    """ Test the open node autotest interface

    Run tests with socat to be close to serial_redirection """

    def setUp(self):
        port = node_connection.OpenNodeConnection.PORT
        tcp_listen = 'tcp4-listen:{port},reuseaddr,fork'.format(port=port)
        cmd = ['socat', '-', tcp_listen]
        self.redirect = Popen(cmd, stdout=PIPE, stdin=PIPE)

        self.on_thread = threading.Thread(target=self._open_node_thread)
        self.on_thread.start()

    def tearDown(self):
        self.redirect.terminate()
        self.on_thread.join()

    def _open_node_thread(self):
        try:
            while True:
                line = self.redirect.stdout.readline()
                if not line:
                    break
                self.redirect.stdin.write('READ_LINE %s' % line)
        except (AttributeError, IOError) as err:
            print err
        else:
            print "_open_node_thread stopped"

    def test_sending_multiple_commands(self):
        with node_connection.OpenNodeConnection() as conn:

            cmd = ['cmd']
            ret = conn.send_command(cmd)
            self.assertEquals(['READ_LINE'] + cmd, ret)

            cmd = ['command', 'arg1', 'arg2']
            ret = conn.send_command(cmd)
            self.assertEquals(['READ_LINE'] + cmd, ret)

            cmd = ['command3', 'arg1', 'arg2', 'arg3', 'arg4']
            ret = conn.send_command(cmd)
            self.assertEquals(['READ_LINE'] + cmd, ret)

    def test_sending_one_command(self):
        cmd = ['cmd']
        ret = node_connection.OpenNodeConnection.send_one_command(cmd)
        self.assertEquals(['READ_LINE'] + cmd, ret)

        cmd = ['command', 'arg1', 'arg2']
        ret = node_connection.OpenNodeConnection.send_one_command(cmd)
        self.assertEquals(['READ_LINE'] + cmd, ret)

        cmd = ['command3', 'arg1', 'arg2', 'arg3', 'arg4']
        ret = node_connection.OpenNodeConnection.send_one_command(cmd)
        self.assertEquals(['READ_LINE'] + cmd, ret)

    def test_no_answer(self):
        # Disable node answers
        self.redirect.stdin = mock.Mock()

        ret = node_connection.OpenNodeConnection.send_one_command(['cmd'])
        self.assertEquals(None, ret)


class TestOpenNodeConnectionErrors(unittest.TestCase):

    def test_connection_error(self):
        self.assertRaises(IOError,
                          node_connection.OpenNodeConnection.try_connect,
                          ('localhost', 20000), tries=2, step=0.1)

    def test_context_manager_error(self):
        with self.assertRaises(RuntimeError):
            with node_connection.OpenNodeConnection() as _:
                self.fail('Should not have entered context manager')
