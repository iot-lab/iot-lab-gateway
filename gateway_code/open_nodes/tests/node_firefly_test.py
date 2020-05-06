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

""" gateway_code.open_nodes.node_firefly unit tests files """

import unittest
from mock import patch, Mock

from gateway_code.open_nodes.node_firefly import NodeFirefly


@patch('gateway_code.common.wait_tty')
class TestNodeFirefly(unittest.TestCase):
    """Unittest class for firefly nodes."""

    def setUp(self):
        self.node = NodeFirefly()
        self.fw_path = '/path/to/firmware'
        cc2538_class = patch('gateway_code.utils.cc2538.CC2538').start()
        self.node.cc2538 = cc2538_class.return_value
        self.node.cc2538.flash.return_value = 0
        self.node.cc2538.reset.return_value = 0
        self.node.serial_redirection.start = Mock()
        self.node.serial_redirection.start.return_value = 0
        self.node.serial_redirection.stop = Mock()
        self.node.serial_redirection.stop.return_value = 0

    def tearDown(self):
        patch.stopall()

    def test_basic(self, wait_tty):
        """Test basic functions of a firefly node."""
        # Reset the node
        wait_tty.return_value = 0
        assert self.node.reset() == 0
        assert wait_tty.call_count == 0

        # Node status always returns 0
        assert NodeFirefly.status() == 0

        # programmer instance
        assert self.node.programmer == self.node.cc2538

    @patch('gateway_code.common.wait_no_tty')
    def test_setup(self, wait_no_tty, wait_tty):
        """Test setup function of a firefly node."""
        wait_no_tty.return_value = 0
        wait_tty.return_value = 0
        assert self.node.setup(self.fw_path) == 0
        wait_tty.assert_called_once()
        wait_no_tty.assert_called_once()
        self.node.cc2538.flash.assert_called_once()
        self.node.cc2538.flash.assert_called_with(self.fw_path)
        self.node.serial_redirection.start.assert_called_once()
        assert self.node.serial_redirection.stop.call_count == 0

    @patch('gateway_code.common.wait_no_tty')
    def test_teardown(self, wait_no_tty, wait_tty):
        """Test teardown of a firefly node."""
        wait_no_tty.return_value = 0
        wait_tty.return_value = 0
        # Teardown the node
        assert self.node.teardown() == 0
        self.node.cc2538.flash.assert_called_with(self.node.FW_IDLE)
        wait_tty.assert_called_once()
        wait_no_tty.assert_called_once()
        self.node.serial_redirection.stop.assert_called_once()
        assert self.node.serial_redirection.start.call_count == 0

    @patch('gateway_code.common.wait_no_tty')
    def test_flash(self, wait_no_tty, wait_tty):
        """Test flash of a firefly node."""
        wait_no_tty.return_value = 0
        wait_tty.return_value = 0
        # Flash a firmware
        assert self.node.flash(self.fw_path) == 0
        self.node.cc2538.flash.assert_called_with(self.fw_path)
        assert wait_tty.call_count == 0
        assert wait_no_tty.call_count == 0

        # verify binary mode is not supported
        assert self.node.flash(self.fw_path, binary=True) == 1

        # verify binary offset is not supported
        assert self.node.flash(self.fw_path, binary=False, offset=42) == 1

        # Flash idle firmware
        assert self.node.flash() == 0
        self.node.cc2538.flash.assert_called_with(self.node.FW_IDLE)
        assert wait_tty.call_count == 0
        assert wait_no_tty.call_count == 0
