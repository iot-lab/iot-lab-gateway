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

""" gateway_code.open_nodes.node_atmega256rfr2 unit tests files """

import unittest
from mock import patch, Mock

from gateway_code.open_nodes.node_atmega256rfr2 import NodeAtmega256rfr2


class TestNodeAtmega256rfr2(unittest.TestCase):
    """Unittest class for atmega256rfr2 nodes."""

    def setUp(self):
        self.node = NodeAtmega256rfr2()
        self.fw_path = '/path/to/firmware'
        avrdude_class = patch('gateway_code.utils.avrdude.AvrDude').start()
        self.node.avrdude = avrdude_class.return_value
        self.node.avrdude.flash.return_value = 0
        self.node.avrdude.reset.return_value = 0
        self.node.serial_redirection.start = Mock()
        self.node.serial_redirection.start.return_value = 0
        self.node.serial_redirection.stop = Mock()
        self.node.serial_redirection.stop.return_value = 0

    def tearDown(self):
        patch.stopall()

    def test_basic(self):
        """Test basic functions of a leonardo node."""
        # Reset the node
        assert self.node.reset() == 0

        # Node status always returns 0
        assert NodeAtmega256rfr2.status() == 0

        # programmer is avrdude
        assert self.node.programmer == self.node.avrdude

    @patch('gateway_code.common.wait_tty')
    @patch('gateway_code.common.wait_no_tty')
    def test_setup(self, wait_no_tty, wait_tty):
        """Test setup function of a atmega256rfr2 node."""
        wait_no_tty.return_value = 0
        wait_tty.return_value = 0
        assert self.node.setup(self.fw_path) == 0
        assert wait_tty.call_count == 1
        assert wait_no_tty.call_count == 1
        assert self.node.avrdude.flash.call_count == 1
        self.node.avrdude.flash.assert_called_once()
        self.node.avrdude.flash.assert_called_with(self.fw_path)
        self.node.serial_redirection.start.assert_called_once()
        assert self.node.serial_redirection.stop.call_count == 0

    @patch('gateway_code.common.wait_tty')
    @patch('gateway_code.common.wait_no_tty')
    def test_teardown(self, wait_no_tty, wait_tty):
        """Test teardown of a atmega256rfr2 node."""
        wait_no_tty.return_value = 0
        wait_tty.return_value = 0
        # Teardown the node
        assert self.node.teardown() == 0
        self.node.avrdude.flash.assert_called_with(self.node.FW_IDLE)
        assert wait_tty.call_count == 1
        assert wait_no_tty.call_count == 1
        self.node.serial_redirection.stop.assert_called_once()
        assert self.node.serial_redirection.start.call_count == 0

    def test_flash(self):
        """Test flash of a atmega256rfr2 node."""
        # Flash a firmware
        assert self.node.flash(self.fw_path) == 0
        self.node.avrdude.flash.assert_called_with(self.fw_path)

        # Flash idle firmware
        assert self.node.flash() == 0
        self.node.avrdude.flash.assert_called_with(self.node.FW_IDLE)

        # verify binary mode is not supported
        assert self.node.flash(self.fw_path, binary=True) == 1

        # verify binary offset is not supported
        assert self.node.flash(self.fw_path, binary=False, offset=42) == 1
