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
"""open_nodes package tests."""

import unittest
import mock

from gateway_code.autotest.autotest import FatalError
from gateway_code.open_nodes.node_open_node import NodeOpenNode
from .. import node_class, all_nodes_types
from ..node_m3 import NodeM3
from ..node_a8 import NodeA8

GLOB = 'gateway_code.open_nodes.node_open_node.glob'


class TestsOpenNodes(unittest.TestCase):
    """Test open_nodes package functions."""

    def test_node_class(self):
        """Test loading an open node class."""
        self.assertEquals(NodeM3, node_class('m3'))
        self.assertEquals(NodeA8, node_class('a8'))

    def test_open_node_class_errors(self):
        """Test error while loading an open node class."""
        # No module
        self.assertRaisesRegexp(
            ValueError, '^Board unknown not implemented: ImportError.*$',
            node_class, 'unknown')

        # No Class in module, import node_m3 but required name of class changed
        with mock.patch('gateway_code.open_nodes.OPEN_CLASS_NAME',
                        'UnknownClass'):
            self.assertRaisesRegexp(
                ValueError, '^Board m3 not implemented: AttributeError.*$',
                node_class, 'm3')

    @mock.patch(GLOB, mock.Mock(return_value=['too', 'many', 'dev', 'tty']))
    def test_open_node_board_too_many(self):
        # too many TTY in /dev/iotlab folder
        self.assertRaises(FatalError, lambda: NodeOpenNode())

    @mock.patch(GLOB, mock.Mock(return_value=[]))
    def test_open_node_board_not_enough(self):
        # not enough tty in /dev/iotlab
        self.assertRaises(FatalError, lambda: NodeOpenNode())

    @mock.patch(GLOB, mock.Mock(return_value=['/dev/iotlab/ttyUNRECOGNIZED']))
    def test_open_node_board_unrecognized(self):
        # unrecognized tty
        self.assertRaises(FatalError, lambda: NodeOpenNode())

    def test_open_node_board_class(self):
        # node_class works for open_node
        board_class = node_class('open_node')
        assert board_class == NodeOpenNode

    @mock.patch('gateway_code.open_nodes.node_open_node.node_class')
    @mock.patch('gateway_code.open_nodes.node_open_node.all_nodes_types')
    def test_open_node_board_hijack(self, all_nodes_types, node_class):
        # tests that the hijack works
        assert NodeOpenNode.TTY == 'no board detected yet'

        class MyBoard(object):
            TTY = 'myTTY'

        all_nodes_types.return_value = ['my_board']

        def fake_node_class(value):
            return MyBoard

        node_class.side_effect = fake_node_class

        with mock.patch(GLOB, return_value=[MyBoard.TTY]):

            node = NodeOpenNode()

            assert node.__class__ == MyBoard
            assert node.TTY == MyBoard.TTY


class TestsOpenNodesImplementations(unittest.TestCase):
    """Test loading implemented open nodes implementation."""

    @staticmethod
    def test_nodes_classes():
        """Test loading all implemented open nodes implementation."""
        for node in all_nodes_types():
            # No exception
            print node
            print node_class(node)
