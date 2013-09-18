# -*- coding:utf-8 -*-

import unittest
import mock

import os
import threading
import Queue
from gateway_code import control_node_interface
from gateway_code.control_node_interface import ControlNodeSerial

import sys


class TestControlNodeSerial(unittest.TestCase):

    def setUp(self):
        self.popen_patcher = mock.patch('subprocess.Popen')
        popen_class = self.popen_patcher.start()
        self.popen = popen_class.return_value

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
        self.cn.start(user='harter', exp_id=123)
        self.read_line_called.wait(5)  # wait return None in 2.6
        self.assertTrue(self.read_line_called.is_set())
        self.cn.stop()


    def test_send_command(self):

        self.popen.stderr.readline.return_value = 'start ACK'
        self.popen.stdin.write.side_effect = \
            (lambda *x: self.lock_readline.set())


        self.cn.start(user='harter', exp_id=123)
        self.read_line_called.wait()

        ret = self.cn.send_command(['start', 'DC'])

        self.popen.stderr.readline.return_value = ''
        self.cn.stop()

        self.assertEquals(['start', 'ACK'], ret)



    def test_send_command_no_answer(self):
        self.cn.start(user='harter', exp_id=123)
        self.read_line_called.wait()
        ret = self.cn.send_command(['start', 'DC'])

        self.cn.stop()
        self.assertEquals(None, ret)

    def test_send_command_cn_interface_stoped(self):
        ret = self.cn.send_command(['lala'])
        self.assertEquals(None, ret)



    def test_answer_and_answer_with_queue_full(self):

        self.lock_error = threading.Event()

        self.ret_list = ['reset ACK', 'start ACK', '']
        self.popen.stderr.readline.side_effect = (lambda: self.ret_list.pop(0))

        with mock.patch('gateway_code.control_node_interface.LOGGER.error') \
                as mock_logger:
            mock_logger.side_effect = (lambda *x: self.lock_error.set())

            self.cn.start(user='harter', exp_id=123)
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

            self.cn.start(user='harter', exp_id=123)
            self.read_line_called.wait()
            # started and waiting for data

            self.popen.poll.return_value = 2
            self.lock_readline.set()

            self.lock_error.wait(5)
            self.assertTrue(self.lock_error.is_set())  # wait return None in 2.6

            self.cn.stop()

    def test_stop_before_start(self):
        self.cn.stop()

    def test_stop_with_cn_interface_allready_stopped(self):

        def terminate(*args, **kwargs):
            self.lock_readline.set()
            raise OSError()
        self.popen.terminate.side_effect = terminate

        self.cn.start()
        self.popen.stdin.write.side_effect = IOError()
        ret = self.cn.send_command(['test', 'cmd'])
        self.assertEquals(None, ret)

        self.read_line_called.wait()
        self.lock_readline.set()
        self.cn.stop()

        self.popen.terminate.assert_called()

    def test_stop_and_oml_files_empty(self):

        self.cn.start(user='harter', exp_id=123)
        self.read_line_called.wait()
        # mock file path
        self.cn.oml_files['consumption'] = '/tmp/consumption.oml'
        self.cn.oml_files['radio'] = '/tmp/radio.oml'
        open(self.cn.oml_files['consumption'], 'a').close()
        with open(self.cn.oml_files['radio'], 'a') as _f:
            _f.write('lalala')

        for measure_file in self.cn.oml_files.itervalues():
            open(measure_file, 'a').close()

        self.cn.stop()

        # radio exists, consumption is removed
        os.remove(self.cn.oml_files['radio'])
        self.assertRaises(OSError, os.remove, self.cn.oml_files['consumption'])


    def test_config_oml(self):
        # No user or expid
        ret = self.cn._config_oml(None, None)
        self.assertEquals([], ret)


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
            self.cn._handle_answer('cn_serial_error: any error msg')
            mock_logger.assert_called_with('cn_serial_error: any error msg')

    def test_measures_debug(self):
        self.cn.measures_handler = mock.Mock()
        self.cn._handle_answer('measures_debug: consumption_measure ' +
                               '1377268768.841070:1.78250 ' +
                               '0.000000 3.230000 0.080003')
        self.cn.measures_handler.assert_called_with(
            'measures_debug: consumption_measure ' +
            '1377268768.841070:1.78250 0.000000 3.230000 0.080003')
