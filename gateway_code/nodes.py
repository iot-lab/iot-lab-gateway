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

""" Common logic for plugin nodes classes """

import os
import pkgutil

from gateway_code.utils import elftarget


class MetaNode(type):
    """Metaclass for Control Nodes or Open Nodes"""
    def __init__(cls, name, bases, class_dict):
        type.__init__(cls, name, bases, class_dict)
        if not hasattr(cls, '__registry__'):
            cls.__registry__ = {}
        else:
            if hasattr(cls, 'TYPE'):
                cls.__registry__[cls.TYPE] = cls


class ControlNode(object): # pylint: disable=too-few-public-methods
    """class to inherit for control node classes"""
    __metaclass__ = MetaNode


class OpenNode(object): # pylint: disable=too-few-public-methods
    """class to inherit for open node class"""
    __metaclass__ = MetaNode


# import all the nodes/plugins
def import_all_nodes(pkg_dir):
    """Looks into the given relative path for modules and imports them"""
    pkg_dir = os.path.join(os.path.dirname(__file__), pkg_dir)
    for (module_loader, name, _) in pkgutil.iter_modules([pkg_dir]):
        module_loader.find_module(name).load_module(name)


import_all_nodes('open_nodes')
import_all_nodes('control_nodes')


def _node_class(cld, board_type):
    """Return the open node class implementation for `board_type`.

    :raises ValueError: if board class can't be found """
    try:
        output_class = cld.__registry__[board_type]
        # Class sanity check
        assert output_class.TYPE == board_type
    except KeyError:
        raise ValueError('Board %s not implemented' % board_type)
    else:
        return output_class


def _verify_open_node_class(output_class):
    # Tuple with (class, machine) run 'elftarget.py' on a node firmware
    assert len(output_class.ELF_TARGET) == 2

    for firmware_attr in ('FW_IDLE', 'FW_AUTOTEST'):
        firmware = getattr(output_class, firmware_attr, None)
        assert elftarget.is_compatible_with_node(firmware, output_class), \
            firmware

    required_autotest = {'echo', 'get_time'}  # mandatory
    assert required_autotest.issubset(output_class.AUTOTEST_AVAILABLE)


def open_node_class(board_type):
    """Return the open node class implementation for `board_type`.

    :raises ValueError: if board class can't be found """
    output_class = _node_class(OpenNode, board_type)
    _verify_open_node_class(output_class)
    return output_class


def control_node_class(cn_type):
    """Return the control node class implementation for `cn_type`.

    :raises ValueError: if board class can't be found """
    return _node_class(ControlNode, cn_type)


def all_open_nodes_types():
    """Returns all the open nodes classes"""
    return OpenNode.__registry__.keys()


def all_control_nodes_types():
    """Returns all the control nodes classes"""
    return ControlNode.__registry__.keys()
