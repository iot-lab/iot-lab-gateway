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

""" gateway_code.open_nodes.common.node_edbg unit tests files """

import unittest
from mock import patch, Mock

from gateway_code.nodes import OpenNodeBase
from gateway_code.open_nodes.common.node_edbg import NodeEdbgBase
from gateway_code.open_nodes.node_arduino_zero import NodeArduinoZero


class NodeEdbgTest(NodeEdbgBase):
    """A test node derived from NodeOpenOCDBase."""
    TYPE = 'edbgnode_test'
    TTY = '/dev/iotlab/ttyTestEdbgNode'
    BAUDRATE = 115200
    OPENOCD_CFG_FILE = NodeArduinoZero.OPENOCD_CFG_FILE
    FW_IDLE = NodeArduinoZero.FW_IDLE
    FW_AUTOTEST = NodeArduinoZero.FW_AUTOTEST


class TestNodeEdbgBase(unittest.TestCase):
    """Unittest class for OpenOCD based open nodes."""

    def setUp(self):
        self.node = NodeEdbgTest()
        self.fw_path = '/path/to/firmware'
        openocd_class = patch('gateway_code.utils.openocd.OpenOCD').start()
        self.node.openocd = openocd_class.return_value
        self.node.openocd.flash.return_value = 0
        self.node.openocd.reset.return_value = 0
        self.node.openocd.flash.return_value = 0
        self.node.openocd.debug_start.return_value = 0
        self.node.openocd.debug_stop.return_value = 0
        edbg_class = patch('gateway_code.utils.edbg.Edbg').start()
        self.node.edbg = edbg_class.return_value
        self.node.edbg.flash.return_value = 0
        self.node.serial_redirection.start = Mock()
        self.node.serial_redirection.start.return_value = 0
        self.node.serial_redirection.stop = Mock()
        self.node.serial_redirection.stop.return_value = 0

    def tearDown(self):
        patch.stopall()

    @classmethod
    def tearDownClass(cls):
        # Explicitly clear OpenNodeBase registry at the end of all tests.
        del OpenNodeBase.__registry__[NodeEdbgTest.TYPE]

    def test_edbg_node_basic(self):
        """Test basic functions of an edbg based node."""
        # Reset the node
        assert not self.node.reset()
        self.node.openocd.reset.assert_called_once()

        # Node status always returns 0
        assert NodeEdbgTest.status() == 0

        # debug start
        assert self.node.debug_start() == 0

        # debug stop
        assert self.node.debug_stop() == 0

    @patch('gateway_code.common.wait_tty')
    @patch('gateway_code.common.wait_no_tty')
    def test_edbg_node_flash(self, no_tty, tty):
        """Test flash function of an edbg based node."""
        no_tty.return_value = 0
        tty.return_value = 0
        # Setup the node
        assert self.node.setup(self.fw_path) == 0
        assert self.node.edbg.flash.call_count == 1
        self.node.edbg.flash.assert_called_with(self.fw_path)

        # Teardown the node
        assert self.node.teardown() == 0
        self.node.edbg.flash.assert_called_with(self.node.FW_IDLE)

        # Flash a firmware
        assert self.node.flash(self.fw_path) == 0
        self.node.edbg.flash.assert_called_with(self.fw_path)

        assert self.node.flash() == 0
        self.node.edbg.flash.assert_called_with(self.node.FW_IDLE)

    @patch('gateway_code.common.wait_tty')
    @patch('gateway_code.common.wait_no_tty')
    def test_edbg_node_flash_with_debug(self, no_tty, tty):
        # pylint:disable=protected-access
        """Test flash function of an edbg based node while in debug session."""
        no_tty.return_value = 0
        tty.return_value = 0
        # Setup the node
        assert self.node.debug_start() == 0
        assert self.node.edbg.flash.call_count == 0
        assert self.node.openocd.flash.call_count == 0  # No current firmware
        assert self.node._in_debug

        # Stop de debug session
        assert self.node.debug_stop() == 0
        assert self.node.openocd.flash.call_count == 0
        assert not self.node._in_debug

        # Test with an already flashed firmware
        self.node.flash(self.node.FW_AUTOTEST)
        assert self.node.edbg.flash.call_count == 1
        assert self.node.debug_start() == 0
        assert self.node.edbg.flash.call_count == 1
        assert self.node.openocd.flash.call_count == 1
        self.node.openocd.flash.assert_called_with(self.node._current_fw)
        assert self.node._current_fw == self.node.FW_AUTOTEST
        assert self.node._in_debug

        # Stop de debug session
        assert self.node.debug_stop() == 0
        assert self.node.openocd.flash.call_count == 1
        assert not self.node._in_debug
