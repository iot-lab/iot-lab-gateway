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

""" gateway_code.open_nodes.node_zigduino unit tests files """

import os
import tempfile
import unittest
from serial import SerialException
from mock import patch, Mock

from gateway_code.open_nodes.node_zigduino import NodeZigduino


@patch('gateway_code.common.wait_tty')
class TestNodeZigduino(unittest.TestCase):
    """Unittest class for zigduino nodes."""

    def setUp(self):
        self.node = NodeZigduino()
        self.node.TTY = tempfile.NamedTemporaryFile(delete=False).name
        self.fw_path = '/path/to/firmware'
        avrdude_class = patch('gateway_code.utils.avrdude.AvrDude').start()
        self.node.avrdude = avrdude_class.return_value
        self.node.avrdude.flash.return_value = 0
        self.node.serial_redirection.start = Mock()
        self.node.serial_redirection.start.return_value = 0
        self.node.serial_redirection.stop = Mock()
        self.node.serial_redirection.stop.return_value = 0
        self.serial = patch('serial.Serial').start()
        termios_get = patch('termios.tcgetattr').start()
        termios_get.return_value = [1, 2, 3]
        termios_set = patch('termios.tcsetattr').start()
        termios_set.return_value = 0

    def tearDown(self):
        os.remove(self.node.TTY)
        patch.stopall()

    def test_basic(self, wait_tty):
        """Test basic functions of a zigduino node."""
        # Node status always returns 0
        assert self.node.status() == 0

        # programmer instance
        assert self.node.programmer == self.node.avrdude

        # Reset the node
        wait_tty.return_value = 0
        assert self.node.reset() == 0
        wait_tty.assert_called_once()

        # Reset with OSError raise by serial setDTR => just a warning is
        # displayed
        wait_tty.call_count = 0
        self.serial.return_value.close = Mock(side_effect=OSError())
        assert self.node.reset() == 0
        assert wait_tty.call_count == 1

        # Reset with serial error
        wait_tty.call_count = 0
        self.serial.side_effect = SerialException('Error')
        assert self.node.reset() == 1
        assert wait_tty.call_count == 0

    @patch('gateway_code.common.wait_no_tty')
    def test_setup(self, wait_no_tty, wait_tty):
        """Test setup function of a zigduino node."""
        wait_no_tty.return_value = 0
        wait_tty.return_value = 0
        # Setup the node
        assert self.node.setup(self.fw_path) == 0
        assert wait_tty.call_count == 3
        assert wait_no_tty.call_count == 2
        assert self.node.avrdude.flash.call_count == 1
        self.node.avrdude.flash.assert_called_once()
        self.node.avrdude.flash.assert_called_with(self.fw_path)
        self.node.serial_redirection.start.assert_called_once()
        assert self.node.serial_redirection.stop.call_count == 0

        # Setup with serial error
        wait_tty.call_count = 0
        wait_no_tty.call_count = 0
        self.serial.side_effect = SerialException('Error')
        assert self.node.setup(self.fw_path) == 1
        assert wait_tty.call_count == 3
        assert wait_no_tty.call_count == 2

    @patch('gateway_code.common.wait_no_tty')
    def test_teardown(self, wait_no_tty, wait_tty):
        """Test teardown of a zigduino node."""
        wait_no_tty.return_value = 0
        wait_tty.return_value = 0
        assert self.node.teardown() == 0
        assert wait_tty.call_count == 4
        assert wait_no_tty.call_count == 2
        self.node.avrdude.flash.assert_called_with(self.node.FW_IDLE)
        self.node.serial_redirection.stop.assert_called_once()
        assert self.node.serial_redirection.start.call_count == 0

    @patch('gateway_code.common.wait_no_tty')
    def test_flash(self, wait_no_tty, wait_tty):
        """Test flash of a zigduino node."""
        wait_no_tty.return_value = 0
        wait_tty.return_value = 0
        # Flash a firmware
        assert self.node.flash(self.fw_path) == 0
        assert wait_tty.call_count == 2
        assert wait_no_tty.call_count == 1
        self.node.avrdude.flash.assert_called_with(self.fw_path)
        self.node.serial_redirection.stop.assert_called_once()
        self.node.serial_redirection.start.assert_called_once()

        # verify binary mode is not supported
        assert self.node.flash(self.fw_path, binary=True) == 1

        # verify binary offset is not supported
        assert self.node.flash(self.fw_path, binary=False, offset=42) == 1

        # Flash idle firmware
        wait_tty.call_count = 0
        wait_no_tty.call_count = 0
        assert self.node.flash() == 0
        assert wait_tty.call_count == 2
        assert wait_no_tty.call_count == 1
        self.node.avrdude.flash.assert_called_with(self.node.FW_IDLE)
