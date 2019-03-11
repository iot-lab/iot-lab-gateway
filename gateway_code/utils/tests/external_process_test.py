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


""" test external_process module """

import os
import time
import shlex
import logging
import itertools
import signal
import unittest

import mock
from testfixtures import LogCapture

from ..external_process import ExternalProcess
from ..serial_redirection import SerialRedirection
from ..rtl_tcp import RtlTcp
from ..mjpg_streamer import MjpgStreamer
from ..mosquitto import Mosquitto
from ..lora_gateway_bridge import (LoraGatewayBridge, LORA_GATEWAY_BRIDGE_CMD,
                                   LORA_GATEWAY_BRIDGE)

# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint <= 1.3
# pylint: disable=too-many-public-methods
# pylint >= 1.4
# pylint: disable=too-few-public-methods
# pylint: disable=no-member

CURRENT_DIR = os.path.dirname(__file__)

TTY_TEST = '/tmp/ttySRT'
BAUDRATE_TEST = '500000'
RTL_PORT_TEST = '50000'
RTL_FREQ_TEST = '86800000'
CAMERA_PORT_TEST = '40000'
MOSQUITTO_PORT_TEST = '1883'

LOGGER = logging.getLogger('gateway_code')


class _DummyProcess(ExternalProcess):
    """ Class implementing a dummy process

    It's implemented as a stoppable thread running top in a loop.
    """
    TOP = ('/usr/bin/top')
    NAME = "dummy"

    def __init__(self):
        self.process_cmd = shlex.split(self.TOP)
        self.stdout = open(os.devnull, 'w')
        super(_DummyProcess, self).__init__()

    def check_error(self, retcode):
        """Print debug message and check error."""
        if retcode and self._run:
            LOGGER.warning('%s error or restarted', self.NAME)
        return retcode


class TestComplexExternalProcessStop(unittest.TestCase):
    """Test External process complex stop cases."""

    @mock.patch('subprocess.Popen')
    def test_terminate_non_running_process(self, m_popen):
        """ Test the case where 'stop' is called on a process that is currently
        being restarted.
        It can happen if stop is called after an error """

        process = _DummyProcess()
        m_process = process.process
        m_process = m_popen.return_value
        m_process.send_signal.side_effect = OSError(3, "No such process")

        process.start()
        time.sleep(2)
        process.stop()

        self.assertTrue(m_process.send_signal.called)

    @mock.patch('gateway_code.utils.mjpg_streamer.MJPG_STREAMER_LOG_FILE',
                '/tmp/mjpg_streamer_test.log')
    def test_process_needs_sigkill(self):
        """Test cases where send_signal must be called multiple times."""
        log = LogCapture('gateway_code', level=logging.WARNING)
        self.addCleanup(log.uninstall)

        only_sigkill = os.path.join(CURRENT_DIR, 'only_sigkill.py')
        only_sigkill = 'python %s' % only_sigkill

        with mock.patch.object(_DummyProcess, 'TOP', only_sigkill):
            m_process = _DummyProcess()
            m_process.start()
            time.sleep(5)
            m_process.stop()

        log.check(('gateway_code', 'WARNING',
                   'External process signal: escalading to SIGKILL'))


class TestSignalsIter(unittest.TestCase):
    """ExternalProcess.signals_iter."""

    def test_signals_iter(self):
        """Test default signals_iter configuration."""
        signals_iter = _DummyProcess.signals_iter()
        signals = list(itertools.islice(signals_iter, 0, 32))
        expected = [
            signal.SIGTERM, signal.SIGTERM, signal.SIGTERM, signal.SIGTERM,
            signal.SIGTERM, signal.SIGTERM, signal.SIGTERM, signal.SIGTERM,
            signal.SIGTERM, signal.SIGTERM,
            signal.SIGINT, signal.SIGINT, signal.SIGINT, signal.SIGINT,
            signal.SIGINT, signal.SIGINT, signal.SIGINT, signal.SIGINT,
            signal.SIGINT, signal.SIGINT,
            signal.SIGKILL, signal.SIGKILL, signal.SIGKILL, signal.SIGKILL,
            signal.SIGKILL, signal.SIGKILL, signal.SIGKILL, signal.SIGKILL,
            signal.SIGKILL, signal.SIGKILL, signal.SIGKILL, signal.SIGKILL,
        ]

        self.assertEqual(signals, expected)

    def test_signals_iter_config(self):
        """Test configuring signals_iter."""
        signals_iter = _DummyProcess.signals_iter(sigterm=1, sigint=0)
        signals = list(itertools.islice(signals_iter, 0, 3))

        expected = [signal.SIGTERM, signal.SIGKILL, signal.SIGKILL]
        self.assertEqual(signals, expected)


@mock.patch('subprocess.Popen')
class TestProcessSocat(unittest.TestCase):
    """SerialRedirection._call_process."""

    def test__call_socat_error(self, m_popen):
        """ Test the _call_process error case """
        m_popen.return_value.wait.return_value = -1
        m_redirect = SerialRedirection(TTY_TEST, BAUDRATE_TEST)
        m_redirect._run = True

        ret = m_redirect._call_process(m_redirect.stdout)
        self.assertEqual(-1, ret)

    def test__call_socat_error_tty_not_found(self, m_popen):
        """ Test the _call_process error case when path can't be found"""
        m_popen.return_value.wait.return_value = -1
        m_redirect = SerialRedirection('/dev/NotATty', BAUDRATE_TEST)
        m_redirect._run = True

        ret = m_redirect._call_process(m_redirect.stdout)
        self.assertEqual(-1, ret)


@mock.patch('subprocess.Popen')
class TestProcessRtlTcp(unittest.TestCase):
    """RtlTcp._call_process."""

    def test__call_rtl_tcp_error(self, m_popen):
        """ Test the _call_process error case """
        m_popen.return_value.wait.return_value = -1
        m_rtl_tcp = RtlTcp(RTL_PORT_TEST, RTL_FREQ_TEST)
        m_rtl_tcp._run = True

        ret = m_rtl_tcp._call_process(m_rtl_tcp.stdout)
        self.assertEqual(-1, ret)


@mock.patch('subprocess.Popen')
class TestProcessMjpgStreamer(unittest.TestCase):
    """MjpgStreamer._call_process."""

    @mock.patch('gateway_code.utils.mjpg_streamer.MJPG_STREAMER_LOG_FILE',
                '/tmp/mjpg_streamer_test.log')
    def test__call_mjpg_streamer_error(self, m_popen):
        """ Test the _call_process error case """
        m_popen.return_value.wait.return_value = -1
        m_mjpg_streamer = MjpgStreamer(CAMERA_PORT_TEST)
        m_mjpg_streamer._run = True

        ret = m_mjpg_streamer._call_process(m_mjpg_streamer.stdout)
        self.assertEqual(-1, ret)


@mock.patch('subprocess.Popen')
class TestProcessMosquitto(unittest.TestCase):
    """Mosquitto._call_process."""

    def test__call_mosquitto_error(self, m_popen):
        """ Test the _call_process error case """
        m_popen.return_value.wait.return_value = -1
        m_mosquitto = Mosquitto(MOSQUITTO_PORT_TEST)
        m_mosquitto._run = True

        ret = m_mosquitto._call_process(m_mosquitto.stdout)
        self.assertEqual(-1, ret)


@mock.patch('subprocess.Popen')
class TestProcessLoraGatewayBridge(unittest.TestCase):
    """LoraGatewayBridge._call_process."""

    def test__call_lora_gateway_bridge_error(self, m_popen):
        """ Test the _call_process error case """
        m_popen.return_value.wait.return_value = -1
        m_lora_gateway_bridge = LoraGatewayBridge()
        m_lora_gateway_bridge._run = True

        ret = m_lora_gateway_bridge._call_process(m_lora_gateway_bridge.stdout)
        self.assertEqual(-1, ret)


@mock.patch('gateway_code.utils.lora_gateway_bridge.CFG_DIR', '/tmp')
def test_custom_config_directory():
    """Test when using a custom config directory."""
    _bridge_cfg = os.path.join('/tmp', 'lora-gateway-bridge.toml')
    with open(_bridge_cfg, 'w') as f:
        f.write('test')
    assert os.path.isfile(_bridge_cfg)
    m_lora_gateway_bridge = LoraGatewayBridge()
    expected_cmd = shlex.split(LORA_GATEWAY_BRIDGE_CMD.format(
        bridge=LORA_GATEWAY_BRIDGE, cfg_file=_bridge_cfg))
    assert m_lora_gateway_bridge.process_cmd == expected_cmd
