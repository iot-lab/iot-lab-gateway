# -*- coding:utf-8 -*-

import unittest
import mock

import os
import shutil
import Queue
from gateway_code.control_node_interface import ControlNodeSerial


class TestControlNodeSerial(unittest.TestCase):

    def setUp(self):
        self.popen_patcher = mock.patch('subprocess.Popen')
        popen_class = self.popen_patcher.start()
        self.popen = popen_class.return_value

        self.popen.terminate.side_effect = self._terminate
        self.popen.poll.return_value = None

        self.readline_ret_vals = Queue.Queue(0)
        self.popen.stderr.readline.side_effect = self.readline_ret_vals.get
        self.readline_ret_vals.put('cn_serial_ready\n')

        self.cn = ControlNodeSerial()

    def tearDown(self):
        self.cn.stop()
        self.popen.stop()

    def _terminate(self):
        self.readline_ret_vals.put('')

    def test_normal_start_stop(self):
        ret_start = self.cn.start()
        self.assertEquals(0, ret_start)
        self.popen.stderr.readline.assert_called()

        self.cn.stop()
        self.popen.terminate.assert_called()
        self.assertTrue(self.readline_ret_vals.empty())

    @mock.patch('gateway_code.control_node_interface.LOGGER.error')
    def test_start_error_in_cn_serial(self, mock_logger):

        # poll should return an error
        self.popen.poll.return_value = 2

        ret_start = self.cn.start()
        self.assertNotEquals(0, ret_start)
        mock_logger.assert_called_with(
            'Control node serial reader thread ended prematurely')
        self.cn.stop()

    def test_stop_before_start(self):
        self.cn.stop()

    @mock.patch('gateway_code.control_node_interface.LOGGER.error')
    def test_stop_with_cn_interface_allready_stopped(self, mock_logger):

        # Simulate cn_interface stopped
        self.readline_ret_vals.put('')
        self.popen.stdin.write.side_effect = IOError()
        self.popen.terminate.side_effect = OSError()

        self.cn.start()

        # try sending command
        ret = self.cn.send_command(['test', 'cmd'])
        self.assertEquals(None, ret)
        mock_logger.assert_called_with(
            'control_node_serial process is terminated')

        self.cn.stop()
        mock_logger.assert_called_with(
            'Control node process already terminated')

#
# Test command sending
#
    def test_send_command(self):
        self.popen.stdin.write.side_effect = \
            (lambda *x: self.readline_ret_vals.put('start ACK\n'))

        self.cn.start()
        ret = self.cn.send_command(['start', 'DC'])
        self.assertEquals(['start', 'ACK'], ret)
        self.cn.stop()

    def test_send_command_no_answer(self):
        self.cn.start()
        ret = self.cn.send_command(['start', 'DC'])
        self.assertIsNone(ret)
        self.cn.stop()

    def test_send_command_cn_interface_stoped(self):
        ret = self.cn.send_command(['lala'])
        self.assertIsNone(ret)

    @mock.patch('gateway_code.control_node_interface.LOGGER.error')
    def test_answer_and_answer_with_queue_full(self, mock_logger):
        # get two answers without sending command
        self.readline_ret_vals.put('reset ACK\n')
        self.readline_ret_vals.put('start ACK\n')

        self.cn.start()
        self.cn.stop()

        mock_logger.assert_called_with('Control node answer queue full: %r',
                                       ['start', 'ACK'])

#
# OML specific tests
#
    @mock.patch('gateway_code.config.MEASURES_PATH', '/tmp/{type}/{node_id}')
    def test_stop_and_oml_files_empty(self):

        # setup
        # create measures_dir
        for measure_type in ('consumption', 'radio'):
            shutil.rmtree('/tmp/%s/' % measure_type, ignore_errors=True)
            try:
                os.mkdir('/tmp/%s/' % measure_type)
            except OSError:
                pass

        # append data to radio
        self.cn.start(user='harter', exp_id=123)
        oml_files = self.cn.oml['files']
        with open(oml_files['radio'], 'a') as _file:
            _file.write('lalala')
        self.cn.stop()

        # radio exists, consumption should have been removed
        os.remove(oml_files['radio'])
        self.assertRaises(OSError, os.remove, oml_files['consumption'])

        # teardown
        # remove measures_dir
        for measure_type in ('consumption', 'radio'):
            try:
                os.rmdir('/tmp/%s/' % measure_type)
            except OSError:
                self.fail()

# _config_oml coverage tests

    def test_config_oml(self):
        # No user or expid
        ret = self.cn._config_oml(None, None)
        self.assertEquals([], ret)

    @mock.patch('gateway_code.control_node_interface.LOGGER.error')
    def test_oml_folder_no_measure_folder(self, mock_logger):
        self.assertRaises(IOError, self.cn._config_oml, 'invalid_user_name', 1)
        mock_logger.assert_called()


class TestHandleAnswer(unittest.TestCase):

    def setUp(self):
        self.cn = ControlNodeSerial()

    @mock.patch('gateway_code.control_node_interface.LOGGER.debug')
    def test_config_ack(self, mock_logger):
        self.cn._handle_answer('config_ack reset_time')
        mock_logger.assert_called_with('config_ack %s', 'reset_time')

    @mock.patch('gateway_code.control_node_interface.LOGGER.error')
    def test_error(self, mock_logger):
        self.cn._handle_answer('error 42')
        mock_logger.assert_called_with('Control node error: %r', '42')

    @mock.patch('gateway_code.control_node_interface.LOGGER.error')
    def test_cn_serial_error(self, mock_logger):
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
