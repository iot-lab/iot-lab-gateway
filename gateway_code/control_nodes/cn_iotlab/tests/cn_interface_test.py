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


# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# serial mock note correctly detected
# pylint: disable=maybe-no-member
# pylint: disable=too-many-public-methods

import queue

import unittest
import logging
import mock
from testfixtures import LogCapture

from gateway_code.tests import utils
from .. import cn_interface


class TestControlNodeSerial(unittest.TestCase):

    def setUp(self):
        self.popen_patcher = mock.patch(
            'gateway_code.utils.subprocess_timeout.Popen')
        popen_class = self.popen_patcher.start()
        self.popen = popen_class.return_value

        self.popen.terminate.side_effect = self._terminate
        self.popen.poll.return_value = None

        self.readline_ret_vals = queue.Queue(0)
        self.popen.stderr.readline.side_effect = self.readline_ret_vals.get
        self.readline_ret_vals.put('cn_serial_ready\n')

        self.cn = cn_interface.ControlNodeSerial('tty')
        self.log_error = LogCapture('gateway_code', level=logging.WARNING)

    def tearDown(self):
        self.cn.stop()
        mock.patch.stopall()
        self.log_error.uninstall()

    def _terminate(self):
        self.readline_ret_vals.put('')

    def test_normal_start_stop(self):
        ret_start = self.cn.start()
        self.assertEqual(0, ret_start)
        self.assertTrue(self.popen.stderr.readline.called)

        self.cn.stop()
        self.assertTrue(self.popen.terminate.called)
        self.assertTrue(self.readline_ret_vals.empty())

    def test_start_error_in_cn_serial(self):

        # poll should return an error
        self.popen.poll.return_value = 2

        ret_start = self.cn.start()
        self.assertNotEqual(0, ret_start)
        self.log_error.check(
            ('gateway_code', 'ERROR',
             'Control node serial reader thread ended prematurely'))
        self.cn.stop()

    def test_stop_before_start(self):
        self.cn.stop()

    def test_stop_with_cn_interface_allready_stopped(self):

        # Simulate cn_interface stopped
        self.readline_ret_vals.put('')
        self.popen.stdin.write.side_effect = IOError()
        self.popen.terminate.side_effect = OSError()

        self.cn.start()

        # try sending command
        ret = self.cn.send_command(['test', 'cmd'])
        self.assertEqual(None, ret)
        self.log_error.check(
            ('gateway_code', 'ERROR',
             'control_node_serial process is terminated'))

        self.log_error.clear()
        self.cn.stop()
        self.log_error.check(
            ('gateway_code', 'ERROR',
             'Control node process already terminated'))

    def test_stop_terminate_failed(self):
        """Stop cn_interface but terminate does not stop it."""
        # terminate does not stop process
        self.popen.terminate.side_effect = None
        timeout_expired = cn_interface.subprocess_timeout.TimeoutExpired
        self.popen.wait.side_effect = timeout_expired('cn_serial_interface', 3)
        # kill does it
        self.popen.kill.side_effect = self._terminate

        self.cn.start()
        self.cn.stop()

        self.assertTrue(self.popen.kill.called)
        self.log_error.check(('gateway_code', 'WARNING',
                              'Control node serial not terminated, kill it'))

# Test command sending

    def test_send_command(self):
        self.popen.stdin.write.side_effect = \
            (lambda *x: self.readline_ret_vals.put('start ACK\n'))

        self.cn.start()
        ret = self.cn.send_command(['start', 'DC'])
        self.assertEqual(['start', 'ACK'], ret)
        self.cn.stop()

    def test_send_command_no_answer(self):
        self.cn.start()
        ret = self.cn.send_command(['start', 'DC'])
        self.assertIsNone(ret)
        self.cn.stop()

    def test_send_command_cn_interface_stoped(self):
        ret = self.cn.send_command(['lala'])
        self.assertIsNone(ret)

    def test_answer_and_answer_with_queue_full(self):
        # get two answers without sending command
        self.readline_ret_vals.put('set ACK\n')
        self.readline_ret_vals.put('start ACK\n')

        self.cn.start()
        self.cn.stop()

        self.log_error.check(
            ('gateway_code', 'ERROR',
             'Control node answer queue full: {}'.format(['start', 'ACK'])))

# _cn_interface_args

    def test__cn_interface_args(self):
        args = self.cn._cn_interface_args()
        self.assertIn(self.cn.tty, args)
        self.assertNotIn('-c', args)
        self.assertNotIn('-d', args)

        # OML config
        args = self.cn._cn_interface_args('<omlc></omlc>')
        self.assertIn('-c', args)
        self.assertNotIn('-d', args)
        self.cn._oml_cfg_file.close()

        # Debug mode
        self.cn.measures_debug = (lambda x: None)
        args = self.cn._cn_interface_args()
        self.assertNotIn('-c', args)
        self.assertIn('-d', args)

# _config_oml coverage tests

    def test_empty_config_oml(self):
        # No experiment description
        ret = self.cn._oml_config_file(None)
        self.assertIsNone(ret)

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('m3'))
    def test_config_oml(self):
        oml_xml_cfg = '''<omlc id='{node_id}' exp_id='{exp_id}'>\n</omlc>'''
        self.cn.start(oml_xml_cfg)
        self.assertIsNotNone(self.cn._oml_cfg_file)

        self.cn.stop()

    def test_oml_xml_config(self):
        exp_files = {
            'consumption': '/tmp/consumption',
            'radio': '/tmp/radio',
            'event': '/tmp/event',
            'sniffer': '/tmp/sniffer',
            'log': '/tmp/log',
        }

        oml_xml_cfg = self.cn.oml_xml_config('m3-1', '1234', exp_files)
        self.assertIsNotNone(oml_xml_cfg)
        self.assertTrue(oml_xml_cfg.startswith('<omlc'))

        # No output if none or empty
        oml_xml_cfg = self.cn.oml_xml_config('m3-1', '1234', None)
        self.assertIsNone(oml_xml_cfg)
        oml_xml_cfg = self.cn.oml_xml_config('m3-1', '1234', {})
        self.assertIsNone(oml_xml_cfg)


class TestHandleAnswer(unittest.TestCase):

    def setUp(self):
        self.cn = cn_interface.ControlNodeSerial('tty')
        self.log = LogCapture('gateway_code', level=logging.DEBUG)

    def tearDown(self):
        self.log.uninstall()

    def test_config_ack(self):
        self.cn._handle_answer('config_ack set_time 0.123456')
        self.log.check(
            ('gateway_code', 'DEBUG', 'config_ack set_time'),
            ('gateway_code', 'INFO', 'Control Node set time delay: 123456 us')
        )

        self.log.clear()
        self.cn._handle_answer('config_ack anything')
        self.log.check(
            ('gateway_code', 'DEBUG', 'config_ack anything'),
        )

    def test_error(self):
        self.cn._handle_answer('error 42')
        self.log.check(
            ('gateway_code', 'ERROR', 'Control node error: %r' % '42'))

    def test_cn_serial_error(self):
        self.cn._handle_answer('cn_serial_error: any error msg')
        self.log.check(
            ('gateway_code', 'ERROR', 'cn_serial_error: any error msg'))

    def test_measures_debug(self):
        msg = ('measures_debug: consumption_measure 1377268768.841070:'
               '1.78250 0.000000 3.230000 0.080003')

        m_debug = mock.Mock()

        self.cn.measures_debug = m_debug
        self.cn._handle_answer(msg)
        m_debug.assert_called_with(msg)

        m_debug.reset_mock()
        self.cn.measures_debug = None
        self.cn._handle_answer(msg)
        self.assertFalse(m_debug.called)
