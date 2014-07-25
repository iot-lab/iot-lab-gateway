# -*- coding:utf-8 -*-

""" Test m3_node_interface module """

import unittest
import mock

import threading
import Queue
from gateway_code.autotest import m3_node_interface

# errors when analysing self.serial
# pylint: disable=maybe-no-member
# pylint: disable=missing-docstring
# pylint: disable=too-many-public-methods


class TestOpenNodeSerial(unittest.TestCase):

    """ Test the open node autotest interface """

    def setUp(self):
        self.on_interface = m3_node_interface.OpenNodeSerial()
        self.serial_patcher = mock.patch('serial.Serial')
        serial_class = self.serial_patcher.start()
        self.serial = serial_class.return_value

        self.readline_called = threading.Event()
        self.serial.readline.side_effect = self.readline_mock
        self.serial.readline.return_value = ''

    def readline_mock(self):
        self.readline_called.set()
        self.on_interface.stop_reader.wait()
        return mock.DEFAULT

    def tearDown(self):
        self.serial_patcher.stop()

    def test_start_stop(self):
        self.on_interface.start()
        self.readline_called.wait(5)
        self.assertTrue(self.readline_called.is_set())
        self.on_interface.stop()
        self.serial.close.assert_called()

    def test_start_serial_exception(self):
        from serial import SerialException
        self.serial.flushInput.side_effect = SerialException("ERROR_TEST")
        ret = self.on_interface.start()
        self.assertEquals((1, "ERROR_TEST"), ret)

    @mock.patch('Queue.Queue')
    def test_serial_send_cmd(self, mock_queue_class):
        mock_queue = mock_queue_class.return_value
        # reinit interface to apply mock
        self.on_interface = m3_node_interface.OpenNodeSerial()
        self.on_interface.start()

        # got answer
        mock_queue.get.return_value = 'ACK get_time'
        ret = self.on_interface.send_command(['get_time'])
        self.assertEquals(ret, ['ACK', 'get_time'])

        # no answer
        mock_queue.get.side_effect = Queue.Empty
        ret = self.on_interface.send_command(['test_command', 'with_timeout'])
        self.assertEquals(ret, None)
        self.serial.write.assertCalledWith('test_command with_timeout\n')

        self.on_interface.stop()

    @mock.patch('Queue.Queue')
    def test_serial_reader(self, mock_queue_class):
        mock_queue = mock_queue_class.return_value

        readline_ret_list = ['begin of ', 'complete answer\n']

        def readline_mock():
            """ Return values from readline_ret_list """
            if len(readline_ret_list) == 0:
                self.readline_called.set()
                self.on_interface.stop_reader.wait()
                ret = ''
            else:
                ret = readline_ret_list.pop(0)
            return ret
        self.serial.readline.side_effect = readline_mock

        # reinit interface to apply mock
        self.on_interface = m3_node_interface.OpenNodeSerial()
        self.on_interface.start()
        self.readline_called.wait(5)
        self.assertTrue(self.readline_called.is_set())
        self.on_interface.stop()

        mock_queue.put.assert_called_with('begin of complete answer')
