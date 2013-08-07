# -*- coding:utf-8 -*-

import unittest
import mock


import threading
import Queue
from gateway_code import control_node_interface
from gateway_code.control_node_interface import ControlNodeSerial

import sys


class TestControlNodeSerial(unittest.TestCase):

    def setUp(self):
        self.popen_patcher = mock.patch('subprocess.Popen')
        self.popen_class = self.popen_patcher.start()
        self.popen = self.popen_class.return_value

        self.popen.terminate.side_effect = self._terminate
        self.popen.poll.side_effect = self._poll
        self.popen.poll.return_value = None

        self.popen.stderr.readline.side_effect = self._readline
        self.popen.stderr.readline.return_value = ''

        self.lock_readline = threading.Event()
        self.read_line_called = threading.Event()


        self.cn = ControlNodeSerial()

    def tearDown(self):
        self.popen.stop()
        self.cn.stop()

    def _terminate(self):
        self.lock_readline.set()
        pass

    def _poll(self):
        return mock.DEFAULT

    def _readline(self):
        self.read_line_called.set()
        self.lock_readline.wait()
        self.lock_readline.clear()
        return mock.DEFAULT


    def test_normal_stop(self):
        self.cn.start()
        self.read_line_called.wait(5)  # wait return None in 2.6
        self.assertTrue(self.read_line_called.is_set())
        self.cn.stop()


    def test_send_command(self):

        self.popen.stderr.readline.return_value = 'start ACK'
        self.popen.stdin.write.side_effect = \
            (lambda *x: self.lock_readline.set())


        self.cn.start()
        self.read_line_called.wait()

        ret = self.cn.send_command(['start', 'DC'])

        self.popen.stderr.readline.return_value = ''
        self.cn.stop()

        self.assertEquals(['start', 'ACK'], ret)



    def test_send_command_no_answer(self):
        self.cn.start()
        self.read_line_called.wait()
        ret = self.cn.send_command(['start', 'DC'])

        self.cn.stop()
        self.assertEquals(None, ret)



    def test_answer_and_answer_with_queue_full(self):

        self.lock_error = threading.Event()

        self.ret_list = ['reset ACK', 'start ACK', '']
        self.popen.stderr.readline.side_effect = (lambda: self.ret_list.pop(0))

        with mock.patch('gateway_code.control_node_interface.LOGGER.error') \
                as mock_logger:
            mock_logger.side_effect = (lambda *x: self.lock_error.set())

            self.cn.start()
            self.lock_error.wait(5)
            self.assertTrue(self.lock_error.is_set())  # wait return None in 2.6
            self.cn.stop()

            mock_logger.assert_called_with('Control node answer queue full')

    def test_stop_with_poll_not_none(self):

        self.lock_error = threading.Event()
        self.cn._handle_answer = mock.Mock()
        self.popen.stderr.readline.return_value = 'non empty line'

        with mock.patch('gateway_code.control_node_interface.LOGGER.error') \
                as mock_logger:
            mock_logger.side_effect = (lambda *x: self.lock_error.set())

            self.cn.start()
            self.read_line_called.wait()
            # started and waiting for data

            self.popen.poll.return_value = 2
            self.lock_readline.set()

            self.lock_error.wait(5)
            self.assertTrue(self.lock_error.is_set())  # wait return None in 2.6


            self.cn.stop()

    def test_stop_before_start(self):
        self.cn.stop()



class TestHandleAnswer(unittest.TestCase):

    def setUp(self):
        self.cn = ControlNodeSerial()

    def test_config_ack(self):
        with mock.patch('gateway_code.control_node_interface.LOGGER.debug') \
                as mock_logger:
            self.cn._handle_answer('config_ack reset_time')
            mock_logger.assert_called_with('config_ack %s', 'reset_time')

    def test_error(self):
        with mock.patch('gateway_code.control_node_interface.LOGGER.error') \
                as mock_logger:
            self.cn._handle_answer('error 42')
            mock_logger.assert_called_with('Control node error: %r', '42')

    def test_cn_serial_error(self):
        with mock.patch('gateway_code.control_node_interface.LOGGER.error') \
                as mock_logger:
            self.cn._handle_answer('cn_serial_error any error msg')
            mock_logger.assert_called_with('cn_serial_error any error msg')



class TestEmptyQueue(unittest.TestCase):

    def test_empty_queue_one_element(self):

        queue = Queue.Queue(1)
        control_node_interface._empty_queue(queue)
        self.assertTrue(queue.empty())

        queue.put('TEST')
        control_node_interface._empty_queue(queue)
        self.assertTrue(queue.empty())

    def test_empty_queue_multiple_elemements(self):

        queue = Queue.Queue(5)
        control_node_interface._empty_queue(queue)
        self.assertTrue(queue.empty())


        queue.put('1')
        queue.put('2')
        control_node_interface._empty_queue(queue)
        self.assertTrue(queue.empty())


        queue.put('1')
        queue.put('2')
        queue.put('3')
        queue.put('4')
        queue.put('5')
        control_node_interface._empty_queue(queue)
        self.assertTrue(queue.empty())



