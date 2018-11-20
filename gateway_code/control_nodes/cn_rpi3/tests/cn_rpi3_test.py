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

import os.path
import shutil
import tempfile
import unittest
import mock

from gateway_code.control_nodes.cn_rpi3 import ControlNodeRpi3
from gateway_code.utils import subprocess_timeout


@mock.patch('gateway_code.utils.subprocess_timeout.call')
class TestCnRPI3(unittest.TestCase):
    """Unittest class for RPI3 control node."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.rtl_tcp_conf = os.path.join(self.temp_dir, "rtl_tcp")
        with open(self.rtl_tcp_conf, 'w') as rtl:
            rtl.write('')
        rtl_tcp_conf_mock = os.path.join(self.temp_dir, "log_rtl_tcp")
        self.camera_conf = os.path.join(self.temp_dir, "camera")
        with open(self.camera_conf, 'w') as cam:
            cam.write('')
        camera_conf_mock = os.path.join(self.temp_dir, "log_camera")
        mock.patch('gateway_code.utils.rtl_tcp.RTL_TCP_LOG_FILE',
                   rtl_tcp_conf_mock).start()
        mock.patch('gateway_code.utils.mjpg_streamer.MJPG_STREAMER_LOG_FILE',
                   camera_conf_mock).start()

    def tearDown(self):
        mock.patch.stopall()
        shutil.rmtree(self.temp_dir)

    def test_cn_rpi3_basic(self, call):  # pylint:disable=no-self-use
        """Test basic empty features of RPI3 control node."""
        call.return_value = 0

        # Setup doesn't nothing but is required. It always returns 0
        assert ControlNodeRpi3.setup() == 0
        cn_rpi3 = ControlNodeRpi3('test', None)

        # Flash and status does nothing
        assert cn_rpi3.flash() == 0
        assert cn_rpi3.status() == 0
        assert cn_rpi3.autotest_setup(None) == 0
        assert cn_rpi3.autotest_teardown(None) == 0

    def test_cn_rpi3_open_start_stop(self, call):
        """Test open node start calls the right command."""
        call.return_value = 0

        cn_rpi3 = ControlNodeRpi3('test', None)
        cn_rpi3.start('test')

        assert call.call_count == 1
        call.assert_called_with(args=['sudo', 'ykushcmd', 'ykushxs', '-u'])

        assert cn_rpi3.open_node_state == 'start'

        call.call_count = 0
        cn_rpi3.stop()

        assert call.call_count == 1
        call.assert_called_with(args=['sudo', 'ykushcmd', 'ykushxs', '-d'])

        assert cn_rpi3.open_node_state == 'stop'

        call.call_count = 0
        with mock.patch('gateway_code.control_nodes.cn_rpi3.RTL_TCP_CONFIG',
                        self.rtl_tcp_conf):
            cn_rpi3.start('test')
            assert call.call_count == 1
            call.assert_called_with(args=['sudo', 'ykushcmd', '-u', '1'])

            assert cn_rpi3.open_node_state == 'start'

            call.call_count = 0
            cn_rpi3.stop()

            assert call.call_count == 1
            call.assert_called_with(args=['sudo', 'ykushcmd', '-d', '1'])

            assert cn_rpi3.open_node_state == 'stop'

    def test_cn_rpi3_timeout(self, call):  # pylint:disable=no-self-use
        """Test open node start/stop with timeout."""
        call.side_effect = subprocess_timeout.TimeoutExpired(mock.Mock("test"),
                                                             'timeout')

        cn_rpi3 = ControlNodeRpi3('test', None)
        ret = cn_rpi3.start('test')

        assert cn_rpi3.open_node_state == 'stop'
        assert ret == 1

        ret = cn_rpi3.stop()

        assert cn_rpi3.open_node_state == 'stop'
        assert ret == 1

    @mock.patch('gateway_code.utils.rtl_tcp.RtlTcp.stop')
    @mock.patch('gateway_code.utils.rtl_tcp.RtlTcp.start')
    @mock.patch('gateway_code.utils.mjpg_streamer.MjpgStreamer.stop')
    @mock.patch('gateway_code.utils.mjpg_streamer.MjpgStreamer.start')
    def test_cn_rpi3_configure_profile(self, cam_start, cam_stop,
                                       rtl_start, rtl_stop, call):
        # pylint:disable=too-many-arguments
        """Test open node profile confguration with start/stop experiment."""
        call.return_value = 0
        cam_start.return_value = 0
        cam_stop.return_value = 0
        rtl_start.return_value = 0
        rtl_stop.return_value = 0
        cn_rpi3 = ControlNodeRpi3('test', None)

        ret = cn_rpi3.start_experiment("test")

        assert ret == 0
        assert cn_rpi3.profile == "test"
        assert call.call_count == 0

        ret = cn_rpi3.stop_experiment()

        assert ret == 0
        assert cn_rpi3.profile is None
        assert call.call_count == 1  # ykush is called once to start the on.
        call.call_count = 0

        with mock.patch('gateway_code.control_nodes.cn_rpi3.RTL_TCP_CONFIG',
                        self.rtl_tcp_conf):
            ret = cn_rpi3.start_experiment("test")

            assert ret == 0
            assert cn_rpi3.profile == "test"
            rtl_start.assert_called_once()
            assert call.call_count == 1
            call.assert_called_with(args=['sudo', 'ykushcmd', '-u', '3'])

            call.call_count = 0
            ret = cn_rpi3.stop_experiment()

            assert ret == 0
            assert cn_rpi3.profile is None
            assert call.call_count == 2
            rtl_stop.assert_called_once()
            call.assert_called_with(args=['sudo', 'ykushcmd', '-d', '3'])

        call.call_count = 0
        with mock.patch('gateway_code.control_nodes.cn_rpi3.CAMERA_CONFIG',
                        self.camera_conf):
            ret = cn_rpi3.start_experiment("test")
            assert ret == 0
            assert cn_rpi3.profile == "test"
            cam_start.assert_called_once()
            assert call.call_count == 0

            ret = cn_rpi3.stop_experiment()
            assert ret == 0
            assert cn_rpi3.profile is None
            cam_stop.assert_called_once()
            assert call.call_count == 1
