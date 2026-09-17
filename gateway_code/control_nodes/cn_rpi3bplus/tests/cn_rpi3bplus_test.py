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

""" gateway_code.control_node (RPI3bplus) unit tests files """

import shutil
import tempfile
import unittest
import mock

from gateway_code.control_nodes.cn_rpi3bplus import ControlNodeRpi3bplus
from gateway_code.utils import subprocess_timeout


@mock.patch('gateway_code.utils.subprocess_timeout.call')
class TestCnRPI3bplus(unittest.TestCase):
    """Unittest class for RPI3bplus control node."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        mock.patch.stopall()
        shutil.rmtree(self.temp_dir)

    def test_cn_rpi3plus_basic(self, call):  # pylint:disable=no-self-use
        """Test basic empty features of RPI3bplus control node."""
        call.return_value = 0

        # Setup doesn't nothing but is required. It always returns 0
        assert ControlNodeRpi3bplus.setup() == 0
        cn_rpi3bplus = ControlNodeRpi3bplus('test', None)

        # Flash and status does nothing
        assert cn_rpi3bplus.flash() == 0
        assert cn_rpi3bplus.status() == 0
        assert cn_rpi3bplus.autotest_setup(None) == 0
        assert cn_rpi3bplus.autotest_teardown(None) == 0
        assert cn_rpi3bplus.programmer is None

    def test_cn_rpi3bplus_open_start_stop(self, call):  # pylint:disable=no-self-use
        """Test open node start calls the right command."""
        call.return_value = 0

        cn_rpi3bplus = ControlNodeRpi3bplus('test', None)

        cn_rpi3bplus.start('test')
        assert call.call_count == 1
        call.assert_called_with(args=['sudo', '/usr/bin/uhubctl',
                                      '-l', '1-1', '-p', '2', '-a', '1'])
        assert cn_rpi3bplus.open_node_state == 'start'

        call.call_count = 0
        cn_rpi3bplus.stop()

        assert call.call_count == 2
        # FIXME: how call two times with mock
        # call.assert_has_calls([call(args=['sudo', '/usr/bin/uhubctl', '-l',
        #                     '1-1', '-p', '2', '-a', '3']),
        #                        call(args=['sudo', 'udevadm', 'trigger',
        #                    '--action=remove', '/sys/bus/usb/devices/1-1.2'])])
        assert cn_rpi3bplus.open_node_state == 'stop'

    def test_cn_rpi3bplus_timeout(self, call):  # pylint:disable=no-self-use
        """Test open node start/stop with timeout."""
        call.side_effect = subprocess_timeout.TimeoutExpired(mock.Mock("test"),
                                                             'timeout')

        cn_rpi3bplus = ControlNodeRpi3bplus('test', None)
        ret = cn_rpi3bplus.start('test')

        assert cn_rpi3bplus.open_node_state == 'stop'
        assert ret == 1

        ret = cn_rpi3bplus.stop()

        assert cn_rpi3bplus.open_node_state == 'stop'
        assert ret == 2
