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
""" open nodes plugins tests """

# pylint: disable=missing-docstring


from __future__ import print_function

import pytest

from gateway_code.nodes import open_node_class, all_open_nodes_types
from gateway_code.open_nodes.node_a8 import NodeA8
from gateway_code.open_nodes.node_m3 import NodeM3


def test_node_class():
    """Test loading essential open node classes."""
    assert NodeM3 == open_node_class('m3')
    assert NodeA8 == open_node_class('a8')


def test_open_node_class_errors():
    """Test error while loading an open node class."""
    # No module
    with pytest.raises(ValueError, match='^Board unknown not implemented*$'):
        open_node_class('unknown')


def test_nodes_classes():
    """Test loading all implemented open nodes implementation."""
    for node in all_open_nodes_types():
        # No exception
        print(node)
        node_class = open_node_class(node)
        node_class()
        print(node_class)
