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

""" gateway_code.open_nodes.common.node_segger unit tests files """

import unittest
from mock import patch, Mock

from gateway_code.open_nodes.common.node_segger import NodeSeggerBase
from gateway_code.open_nodes.node_openmoteb import NodeOpenmoteb


class NodeSeggerTest(NodeSeggerBase):
    """A test node derived from NodeSeggerBase."""
    TYPE = 'seggernode_test'
    TTY = '/dev/iotlab/ttyTestSeggerNode'
    BAUDRATE = 115200
    FW_IDLE = NodeOpenmoteb.FW_IDLE
    FW_AUTOTEST = NodeOpenmoteb.FW_AUTOTEST
    JLINK_DEVICE = "CC2538SF53"
    JLINK_IF = "JTAG"
    JLINK_RESET_FILE = NodeOpenmoteb.JLINK_RESET_FILE
    JLINK_FLASH_ADDR = 0x200000


class TestNodeSeggerBase(unittest.TestCase):
    """Unittest class for segger based open nodes."""

    def setUp(self):
        self.node = NodeSeggerTest()
        self.fw_path = '/path/to/firmware'
        segger_class = patch('gateway_code.utils.segger.Segger').start()
        self.node.segger = segger_class.return_value
        self.node.segger.flash.return_value = 0
        self.node.serial_redirection.start = Mock()
        self.node.serial_redirection.start.return_value = 0
        self.node.serial_redirection.stop = Mock()
        self.node.serial_redirection.stop.return_value = 0

    def tearDown(self):
        patch.stopall()

    def test_segger_node_basic(self):
        """Test basic functions of an segger based node."""
        # Node status always returns 0
        assert self.node.status() == 0
