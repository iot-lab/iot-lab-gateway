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

from .. import node_class, all_nodes_types
from ..node_m3 import NodeM3
from ..node_a8 import NodeA8


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
            ValueError, '^Board unknown not implemented*$',
            node_class, 'unknown')


class TestsOpenNodesImplementations(unittest.TestCase):
    """Test loading implemented open nodes implementation."""

    @staticmethod
    def test_nodes_classes():
        """Test loading all implemented open nodes implementation."""
        for node in all_nodes_types():
            # No exception
            print node
            print node_class(node)
