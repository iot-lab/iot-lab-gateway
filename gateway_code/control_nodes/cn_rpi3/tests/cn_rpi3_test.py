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

""" gateway_code.control_node (RPI3) unit tests files """

import mock

from gateway_code.control_nodes.cn_rpi3 import ControlNodeRpi3
from gateway_code.utils import subprocess_timeout


@mock.patch('gateway_code.utils.rtl_tcp.RTL_TCP_LOG_FILE',
            '/tmp/rtl_tcp_test.log')
@mock.patch('gateway_code.utils.mjpg_streamer.MJPG_STREAMER_LOG_FILE',
            '/tmp/mjpg_streamer_test.log')
def test_rpi3_control_node_basic():
    """Test basic empty features of RPI3 control node."""

    # Setup doesn't nothing but is required. It always returns 0
    assert ControlNodeRpi3.setup() == 0

    # Flash and status does nothing
    cn_rpi3 = ControlNodeRpi3('test', None)
    assert cn_rpi3.flash() == 0
    assert cn_rpi3.status() == 0
    assert cn_rpi3.autotest_setup(None) == 0
    assert cn_rpi3.autotest_teardown(None) == 0


@mock.patch('gateway_code.utils.rtl_tcp.RTL_TCP_LOG_FILE',
            '/tmp/rtl_tcp_test.log')
@mock.patch('gateway_code.utils.mjpg_streamer.MJPG_STREAMER_LOG_FILE',
            '/tmp/mjpg_streamer_test.log')
@mock.patch('gateway_code.utils.subprocess_timeout.call')
def test_rpi3_control_node_start(call):
    """Test open node start calls the right command."""
    call.return_value = 0

    cn_rpi3 = ControlNodeRpi3('test', None)
    cn_rpi3.start('test')

    assert call.call_count == 2
    stop, start = call.mock_calls
    stop.assert_called_with(
        args=['sudo', 'uhubctl', '-p', '2', '-a', '0'])
    start.assert_called_with(
        args=['sudo', 'uhubctl', '-p', '2', '-a', '1'])

    assert cn_rpi3.open_node_state == 'start'


@mock.patch('gateway_code.utils.rtl_tcp.RTL_TCP_LOG_FILE',
            '/tmp/rtl_tcp_test.log')
@mock.patch('gateway_code.utils.mjpg_streamer.MJPG_STREAMER_LOG_FILE',
            '/tmp/mjpg_streamer_test.log')
@mock.patch('gateway_code.utils.subprocess_timeout.call')
def test_rpi3_control_node_stop(call):
    """Test open node start calls the right command."""
    call.return_value = 0

    cn_rpi3 = ControlNodeRpi3('test', None)
    cn_rpi3.stop()

    assert call.call_count == 2
    stop, start = call.mock_calls
    stop.assert_called_with(
        args=['sudo', 'uhubctl', '-p', '2', '-a', '0'])
    start.assert_called_with(
        args=['sudo', 'uhubctl', '-p', '2', '-a', '1'])

    assert cn_rpi3.open_node_state == 'start'


@mock.patch('gateway_code.utils.rtl_tcp.RTL_TCP_LOG_FILE',
            '/tmp/rtl_tcp_test.log')
@mock.patch('gateway_code.utils.mjpg_streamer.MJPG_STREAMER_LOG_FILE',
            '/tmp/mjpg_streamer_test.log')
@mock.patch('gateway_code.utils.subprocess_timeout.call')
def test_rpi3_control_node_timeout(call):
    """Test open node start/stop with timeout."""
    call.side_effect = subprocess_timeout.TimeoutExpired(mock.Mock("test"),
                                                         'timeout')

    cn_rpi3 = ControlNodeRpi3('test', None)
    ret = cn_rpi3.start('test')

    assert cn_rpi3.open_node_state == 'stop'
    assert ret == 2  # 2 processes should fail

    ret = cn_rpi3.stop()

    assert cn_rpi3.open_node_state == 'stop'
    assert ret == 2  # 2 processes should fail


@mock.patch('gateway_code.utils.rtl_tcp.RTL_TCP_LOG_FILE',
            '/tmp/rtl_tcp_test.log')
@mock.patch('gateway_code.utils.mjpg_streamer.MJPG_STREAMER_LOG_FILE',
            '/tmp/mjpg_streamer_test.log')
@mock.patch('gateway_code.utils.subprocess_timeout.call')
def test_rpi3_configure_profile(call):
    """Test open node profile confguration with start/stop experiment."""
    call.return_value = 0
    cn_rpi3 = ControlNodeRpi3('test', None)

    ret = cn_rpi3.start_experiment("test")

    assert ret == 0
    assert cn_rpi3.profile == "test"

    ret = cn_rpi3.stop_experiment()

    assert ret == 0
    assert cn_rpi3.profile is None
