# -*- coding:utf-8 -*-

import unittest
import mock


import threading
import Queue
from gateway_code import open_node_validation_interface

import sys


class TestOpenNodeAutoTestInterface(unittest.TestCase):

    def setUp(self):
        self.on_interface = open_node_validation_interface.OpenNodeSerial()
        self.serial_patcher = mock.patch('serial.Serial')
        serial_class = self.serial_patcher.start()
        self.serial = serial_class.return_value

        self.readline_called = threading.Event()
        self.serial.readline.side_effect = self.readline_mock
        self.serial.readline.return_value = ''

    def readline_mock(self, *args, **kwargs):
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


    def test_send_command(self):
        cmd_ret = ['ANSWER', 'RETURN', 'VALUE']
        def _mock_serial_send_cmd(_serial_data):
            return cmd_ret
        self.on_interface._serial_send_cmd = mock.Mock()
        self.on_interface._serial_send_cmd.side_effect = _mock_serial_send_cmd

        # leds
        self.on_interface._serial_send_cmd.reset_mock()
        ret = self.on_interface.send_command(['leds_on', '7'])
        self.assertEquals(cmd_ret, ret)
        self.on_interface._serial_send_cmd.assert_called()

        self.on_interface._serial_send_cmd.reset_mock()
        ret = self.on_interface.send_command(['leds_blink', '7', '42'])
        self.assertEquals(cmd_ret, ret)
        self.on_interface._serial_send_cmd.assert_called()

        # radio cmds
        self.on_interface._serial_send_cmd.reset_mock()
        ret = self.on_interface.send_command(['radio_pkt', '3dBm', '20'])
        self.assertEquals(cmd_ret, ret)
        self.on_interface._serial_send_cmd.assert_called()

        # get_<sensors>
        self.on_interface._serial_send_cmd.reset_mock()
        ret = self.on_interface.send_command(['get_light'])
        self.assertEquals(cmd_ret, ret)
        self.on_interface._serial_send_cmd.assert_called()

        # test_<feature>
        self.on_interface._serial_send_cmd.reset_mock()
        ret = self.on_interface.send_command(['test_flash'])
        self.assertEquals(cmd_ret, ret)
        self.on_interface._serial_send_cmd.assert_called()

        # invalid command
        self.on_interface._serial_send_cmd.reset_mock()
        self.assertRaises(NotImplementedError, self.on_interface.send_command,
                          ['blabla'])
        self.assertEquals(0, self.on_interface._serial_send_cmd.call_count)


    @mock.patch('Queue.Queue')
    def test_serial_send_cmd(self, mock_queue_class):
        mock_queue = mock_queue_class.return_value
        # reinit interface to apply mock
        self.on_interface = open_node_validation_interface.OpenNodeSerial()
        self.on_interface.start()

        # got answer
        mock_queue.get.return_value = 'SUPER ANSWER'
        ret = self.on_interface._serial_send_cmd(['a', 'b', 'c'])
        self.assertEquals(ret, ['SUPER', 'ANSWER'])

        # no answer
        mock_queue.get.side_effect = Queue.Empty
        ret = self.on_interface._serial_send_cmd(['a', 'b', 'c'])
        self.assertEquals(ret, None)

        self.on_interface.stop()


    @mock.patch('Queue.Queue')
    def test_serial_reader(self, mock_queue_class):
        mock_queue = mock_queue_class.return_value

        readline_ret_list = ['begin of ', 'complete answer\n']
        def readline_mock(*args, **kwargs):
            if len(readline_ret_list) == 0:
                self.readline_called.set()
                self.on_interface.stop_reader.wait()
                ret = ''
            else:
                ret = readline_ret_list.pop(0)
            return ret
        self.serial.readline.side_effect = readline_mock

        # reinit interface to apply mock
        self.on_interface = open_node_validation_interface.OpenNodeSerial()
        self.on_interface.start()
        self.readline_called.wait(5)
        self.assertTrue(self.readline_called.is_set())
        self.on_interface.stop()

        mock_queue.put.assert_called_with('begin of complete answer')


