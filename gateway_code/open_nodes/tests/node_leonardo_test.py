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

""" gateway_code.open_nodes.node_leonardo unit tests files """

import unittest
from mock import patch, Mock

from gateway_code.open_nodes.node_leonardo import NodeLeonardo


@patch('gateway_code.common.wait_tty')
class TestNodeLeonardo(unittest.TestCase):
    """Unittest class for leonardo nodes."""

    def setUp(self):
        self.node = NodeLeonardo()
        self.fw_path = '/path/to/firmware'
        self.trigger_bootloader = patch('gateway_code.utils.avrdude.'
                                        'AvrDude.trigger_bootloader').start()
        self.trigger_bootloader.return_value = 0
        avrdude_class = patch('gateway_code.utils.avrdude.AvrDude').start()
        self.node.avrdude = avrdude_class.return_value
        self.node.avrdude.flash.return_value = 0
        self.node.serial_redirection.start = Mock()
        self.node.serial_redirection.start.return_value = 0
        self.node.serial_redirection.stop = Mock()
        self.node.serial_redirection.stop.return_value = 0

    def tearDown(self):
        patch.stopall()

    def test_basic(self, wait_tty):
        """Test basic functions of a leonardo node."""
        # Reset the node
        wait_tty.return_value = 0
        assert self.node.reset() == 0
        self.trigger_bootloader.assert_called_once()
        wait_tty.assert_called_once()

        # Node status always returns 0
        assert self.node.status() == 0

    @patch('gateway_code.common.wait_no_tty')
    def test_setup(self, wait_no_tty, wait_tty):
        """Test setup function of a leonardo node."""
        wait_no_tty.return_value = 0
        wait_tty.return_value = 0
        assert self.node.setup(self.fw_path) == 0
        assert wait_tty.call_count == 2
        assert wait_no_tty.call_count == 1
        assert self.node.avrdude.flash.call_count == 1
        self.node.avrdude.flash.assert_called_once()
        self.node.avrdude.flash.assert_called_with(self.fw_path)
        self.node.serial_redirection.start.assert_called_once()
        assert self.node.serial_redirection.stop.call_count == 0

    @patch('gateway_code.common.wait_no_tty')
    def test_teardown(self, wait_no_tty, wait_tty):
        """Test teardown of a leonardo node."""
        wait_no_tty.return_value = 0
        wait_tty.return_value = 0
        # Teardown the node
        assert self.node.teardown() == 0
        self.node.avrdude.flash.assert_called_with(self.node.FW_IDLE)
        assert wait_tty.call_count == 2
        assert wait_no_tty.call_count == 1
        self.node.serial_redirection.stop.assert_called_once()
        assert self.node.serial_redirection.start.call_count == 0

    @patch('gateway_code.common.wait_no_tty')
    def test_flash(self, wait_no_tty, wait_tty):
        """Test flash of a leonardo node."""
        wait_no_tty.return_value = 0
        wait_tty.return_value = 0
        # Flash a firmware
        assert self.node.flash(self.fw_path) == 0
        self.node.avrdude.flash.assert_called_with(self.fw_path)
        assert wait_tty.call_count == 1

        # Flash idle firmware
        wait_tty.call_count = 0
        assert self.node.flash() == 0
        self.node.avrdude.flash.assert_called_with(self.node.FW_IDLE)
        assert wait_tty.call_count == 1

        # verify binary mode is not supported
        assert self.node.flash(self.fw_path, binary=True) == 1

        # verify binary offset is not supported
        assert self.node.flash(self.fw_path, binary=False, offset=42) == 1

        # Simulate a bootloader error
        self.trigger_bootloader.return_value = 1
        wait_tty.call_count = 0
        self.node.avrdude.flash.call_count = 0
        assert self.node.flash() == 1
        assert self.node.avrdude.flash.call_count == 0
        assert wait_tty.call_count == 0
