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

""" gateway_code.open_nodes.node_pycom unit tests files """

import shlex

import unittest
import serial
from mock import patch

from gateway_code.open_nodes.node_pycom import NodePycom
from gateway_code.open_nodes.node_pycom import PYCOM_UPDATE_BIN
from gateway_code.open_nodes.node_pycom import PYCOM_FLASH_ERASE_HARD


@patch('serial.Serial')
class TestNodePycom(unittest.TestCase):
    """Unittest class for pycom nodes."""

    def setUp(self):
        self.node = NodePycom()
        self.pycom_str = PYCOM_FLASH_ERASE_HARD.format(bin=PYCOM_UPDATE_BIN,
                                                       port=self.node.TTY)
        patch('time.sleep').start()

    def tearDown(self):
        patch.stopall()

    @patch('subprocess.call')
    @patch('gateway_code.common.wait_tty')
    @patch('gateway_code.utils.external_process.ExternalProcess.start')
    def test_setup(self, serial_start, wait, call, ser):
        """Test pycom node setup."""
        serial_start.return_value = 0
        wait.return_value = 0
        call.return_value = 0

        assert self.node.setup() == 0
        assert call.call_count == 1
        call.assert_called_with(shlex.split(self.pycom_str))
        assert serial_start.call_count == 1
        assert ser.call_count == 3

        serial_start.call_count = 0
        call.call_count = 0
        ser.call_count = 0
        serial_start.return_value = 1
        assert self.node.setup() == 1
        assert call.call_count == 1
        call.assert_called_with(shlex.split(self.pycom_str))
        assert serial_start.call_count == 1
        assert ser.call_count == 3

        serial_start.call_count = 0
        call.call_count = 0
        ser.call_count = 0
        serial_start.return_value = 0
        ser.side_effect = serial.serialutil.SerialException

        assert self.node.setup() == 3
        assert call.call_count == 1
        call.assert_called_with(shlex.split(self.pycom_str))
        assert ser.call_count == 3

    @patch('subprocess.call')
    @patch('gateway_code.utils.external_process.ExternalProcess.stop')
    def test_teardown(self, serial_stop, call, ser):
        """Test pycom node teardown."""
        serial_stop.return_value = 0
        call.return_value = 0

        assert self.node.teardown() == 0
        assert serial_stop.call_count == 1
        assert ser.call_count == 2
        assert call.call_count == 1
        call.assert_called_with(shlex.split(self.pycom_str))

        serial_stop.call_count = 0
        call.call_count = 0
        ser.call_count = 0

        serial_stop.return_value = 1
        assert self.node.teardown() == 1
        assert serial_stop.call_count == 1
        assert ser.call_count == 2
        assert call.call_count == 1
        call.assert_called_with(shlex.split(self.pycom_str))

        serial_stop.call_count = 0
        call.call_count = 0
        ser.call_count = 0
        serial_stop.return_value = 0
        ser.side_effect = serial.serialutil.SerialException

        assert self.node.teardown() == 2
        assert ser.call_count == 2
        assert call.call_count == 1
        call.assert_called_with(shlex.split(self.pycom_str))

    def test_reset(self, ser):
        """Test pycom node reset."""
        assert self.node.reset() == 0
        assert ser.call_count == 1
        ser.assert_called_with(self.node.TTY, self.node.BAUDRATE)

        ser.call_count = 0
        ser.side_effect = serial.serialutil.SerialException

        assert self.node.reset() == 1
        assert ser.call_count == 1
