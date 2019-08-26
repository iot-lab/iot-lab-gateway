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

""" gateway_code.open_nodes.common.node_openocd unit tests files """

import unittest
import serial
from mock import patch, Mock

from gateway_code.nodes import OpenNodeBase
from gateway_code.open_nodes.common.node_openocd import NodeOpenOCDBase
from gateway_code.open_nodes.node_microbit import NodeMicrobit


class NodeOpenOCDTest(NodeOpenOCDBase):
    """A test node derived from NodeOpenOCDBase."""
    TYPE = 'openocd_test'
    TTY = '/dev/iotlab/ttyTestOpenOCD'
    BAUDRATE = 115200
    ROM_START_ADDR = 0xaa
    OPENOCD_CFG_FILE = NodeMicrobit.OPENOCD_CFG_FILE
    FW_IDLE = NodeMicrobit.FW_IDLE
    FW_AUTOTEST = NodeMicrobit.FW_AUTOTEST
    DIRTY_SERIAL = False
    JLINK_SERIAL = False


class TestNodeOpenOCDBase(unittest.TestCase):
    """Unittest class for OpenOCD based open nodes."""

    def setUp(self):
        self.node = NodeOpenOCDTest()
        self.fw_path = '/path/to/firmware'
        openocd_class = patch('gateway_code.utils.openocd.OpenOCD').start()
        self.node.openocd = openocd_class.return_value
        self.node.openocd.flash.return_value = 0
        self.node.openocd.reset.return_value = 0
        self.node.openocd.flash.return_value = 0
        self.node.openocd.debug_start.return_value = 0
        self.node.openocd.debug_stop.return_value = 0
        self.node.serial_redirection.start = Mock()
        self.node.serial_redirection.start.return_value = 0
        self.node.serial_redirection.stop = Mock()
        self.node.serial_redirection.stop.return_value = 0

    def tearDown(self):
        patch.stopall()

    @classmethod
    def tearDownClass(cls):
        # Explicitly clear OpenNodeBase registry at the end of all tests.
        del OpenNodeBase.__registry__[NodeOpenOCDTest.TYPE]

    def test_openocd_node_basic(self):
        """Test basic functions of an openocd based node."""
        # Reset the node
        assert self.node.reset() == 0
        self.node.openocd.reset.assert_called_once()

        # Node status always returns 0
        assert NodeOpenOCDTest.status() == 0

        # debug start
        assert self.node.debug_start() == 0

        # debug stop
        assert self.node.debug_stop() == 0

    @patch('serial.Serial')
    @patch('gateway_code.common.wait_tty')
    @patch('gateway_code.common.wait_no_tty')
    def test_openocd_node_flash(self, no_tty, tty, ser):
        """Test flash function of an openocd based node."""
        no_tty.return_value = 0
        tty.return_value = 0
        # Setup the node
        assert self.node.setup(self.fw_path) == 0
        assert self.node.openocd.flash.call_count == 1
        self.node.openocd.flash.assert_called_with(
            self.fw_path, False, self.node.ROM_START_ADDR)
        assert ser.call_count == 0
        assert tty.call_count == 1

        # Teardown the node
        tty.call_count = 0
        assert self.node.teardown() == 0
        self.node.openocd.flash.assert_called_with(
            self.node.FW_IDLE, False, self.node.ROM_START_ADDR)
        assert tty.call_count == 1

        # Flash a firmware
        assert self.node.flash(self.fw_path) == 0
        tty.call_count = 0
        self.node.openocd.flash.assert_called_with(
            self.fw_path, False, self.node.ROM_START_ADDR)
        assert ser.call_count == 0
        assert tty.call_count == 0

        assert self.node.flash() == 0
        self.node.openocd.flash.assert_called_with(
            self.node.FW_IDLE, False, self.node.ROM_START_ADDR)
        assert ser.call_count == 0
        assert tty.call_count == 0

        # Flash with DIRTY_SERIAL attribute
        # pylint:disable=invalid-name,attribute-defined-outside-init
        with patch('gateway_code.open_nodes.common.tests.node_openocd_test.'
                   'NodeOpenOCDTest.DIRTY_SERIAL', True):
            assert self.node.flash(self.fw_path) == 0
            self.node.openocd.flash.assert_called_with(
                self.fw_path, False, self.node.ROM_START_ADDR)
            assert ser.call_count == 1
            assert tty.call_count == 0

            # Simulate a serial issue
            ser.side_effect = serial.serialutil.SerialException
            assert self.node.flash() == 1
            self.node.openocd.flash.assert_called_with(
                self.node.FW_IDLE, False, self.node.ROM_START_ADDR)

        # Flash with JLINK_SERIAL attribute
        # pylint:disable=invalid-name,attribute-defined-outside-init
        with patch('gateway_code.open_nodes.common.tests.node_openocd_test.'
                   'NodeOpenOCDTest.JLINK_SERIAL', True):
            assert self.node.flash(self.fw_path) == 0
            self.node.openocd.flash.assert_called_with(
                self.fw_path, False, self.node.ROM_START_ADDR)
            assert tty.call_count == 1
