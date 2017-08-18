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

""" gateway_code open node files """

import os
import glob
import importlib
from gateway_code.utils import elftarget


OPEN_NODES_MODULE = 'node_{type}'
OPEN_CLASS_NAME = 'Node{title}'


def node_class(board_type):
    """Return the open node class implementation for `board_type`.

    :raises ValueError: if board class can't be found """
    try:
        module_path = '%s.%s' % (
            __name__, OPEN_NODES_MODULE.format(
                type=board_type.replace('-', '_')))
        class_name = OPEN_CLASS_NAME.format(title=_node_title(board_type))

        # Get node class from board_type
        module = importlib.import_module(module_path)
        board_class = getattr(module, class_name)

        # Class sanity check
        _assert_class_valid(board_class, board_type)
    except (ImportError, AttributeError) as err:
        raise ValueError('Board %s not implemented: %r' % (board_type, err))
    else:
        return board_class


def _node_title(board_type):
    """Format node title in CamelCase from board type.

    >>> _node_title('m3')
    'M3'
    >>> _node_title('arduino_zero')
    'ArduinoZero'
    >>> _node_title('arduino-zero')
    'ArduinoZero'
    >>> _node_title('samr21')
    'Samr21'
    >>> _node_title('st_lrwan1')
    'StLrwan1'
    >>> _node_title('st-lrwan1')
    'StLrwan1'
    """
    return board_type.title().replace('_', '').replace('-', '')


def _assert_class_valid(board_class, board_type):
    """Check expected values on classes."""
    assert board_class.TYPE == board_type
    # Tuple with (class, machine) run 'elftarget.py' on a node firmware
    assert len(board_class.ELF_TARGET) == 2

    for firmware_attr in ('FW_IDLE', 'FW_AUTOTEST'):
        firmware = getattr(board_class, firmware_attr, None)
        assert elftarget.is_compatible_with_node(firmware, board_class), \
            firmware

    required_autotest = {'echo', 'get_time'}  # mandatory
    assert required_autotest.issubset(board_class.AUTOTEST_AVAILABLE)


def all_nodes_types():
    """Find all implemented node types."""

    current_directory = os.path.dirname(__file__)

    open_node_glob = OPEN_NODES_MODULE.format(type='*')
    open_node_glob = '%s.%s' % (open_node_glob, 'py')
    open_node_glob = os.path.join(current_directory, open_node_glob)

    nodes = glob.glob(open_node_glob)
    nodes = [os.path.basename(node) for node in nodes]
    nodes = [node.replace('node_', '') for node in nodes]
    nodes = [node.replace('.py', '') for node in nodes]

    return nodes
