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
        self.read_line_called.wait()
        import time
        self.cn.stop()


    def test_send_command(self):

        def _unlock_readline(*args):
            self.lock_readline.set()

        self.popen.stderr.readline.return_value = 'start ACK'
        self.popen.stdin.write.side_effect = _unlock_readline

        self.cn.start()
        self.read_line_called.wait()
        self.read_line_called.clear()

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
        def log_error(*args):
            self.lock_error.set()


        self.ret_list = ['reset ACK', 'start ACK', '']
        def _readline():
            return self.ret_list.pop(0)

        self.popen.stderr.readline.side_effect = _readline

        with mock.patch('gateway_code.control_node_interface.LOGGER.error') \
                as mock_logger:
            mock_logger.side_effect = log_error

            self.cn.start()
            self.lock_error.wait()
            self.cn.stop()

            mock_logger.assert_called_with('Control node answer queue full')



    def test_stop_with_poll_not_none(self):

        self.counter = 2
        self.lock_error = threading.Event()

        def log_error(*args):
            self.counter -= 1
            if self.counter == 0:
                self.lock_error.set()


        with mock.patch('gateway_code.control_node_interface.LOGGER.error') \
                as mock_logger:
            self.cn.start()
            self.read_line_called.wait()
            self.popen.stderr.readline.return_value = 'error 3'

            self.popen.poll.return_value = 2
            self.lock_readline.set()
            mock_logger.side_effect = log_error


            self.lock_error.wait()
            self.cn.stop()
            self.assertEquals(2, mock_logger.call_count)




    def test_stop_before_start(self):
        self.cn.stop()









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



