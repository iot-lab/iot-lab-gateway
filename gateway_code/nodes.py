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

# pylint: disable=no-member

""" Common logic for plugin nodes classes """
import abc
import os
import inspect
import pkgutil

from gateway_code.utils import elftarget


def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    return meta("NewBase", bases, {})


class NodeBase(with_metaclass(abc.ABCMeta)):
    # pylint: disable=too-few-public-methods
    """ metaclass combining registry and abstract contract """

    @abc.abstractmethod
    def status(self):
        """ Status of the node """
        pass  # pragma: no cover

    @property
    @abc.abstractmethod
    def programmer(self):
        """Returns the programmer instance of an open node."""
        pass  # pragma: no cover


class ControlNodeBase(NodeBase):
    """ Class to inherit, for control node classes """

    @abc.abstractmethod
    def start(self, exp_id, exp_files=None):
        """ This method is called when starting an experiment """
        pass  # pragma: no cover

    @abc.abstractmethod
    def stop(self):
        """ This method is called when stopping an experiment """
        pass  # pragma: no cover

    @abc.abstractmethod
    def start_experiment(self, profile):
        """ Configure experiment and monitoring on ControlNode"""
        pass  # pragma: no cover

    @abc.abstractmethod
    def stop_experiment(self):
        """ Cleanup Control node Monitoring and experiment """
        pass  # pragma: no cover

    @abc.abstractmethod
    def autotest_setup(self, measures_handler):
        """ Setup the control node for the open node autotest """
        pass  # pragma: no cover

    @abc.abstractmethod
    def autotest_teardown(self, stop_on):
        """ Cleanup the control node for the open node autotest """
        pass  # pragma: no cover

    @abc.abstractmethod
    def configure_profile(self, profile=None):
        """ Setup the profile used by the control node """
        pass  # pragma: no cover

    @abc.abstractmethod
    def flash(self, firmware_path=None, binary=False, offset=0):
        """ Flash firmware on the control_node """
        pass  # pragma: no cover


class OpenNodeBase(NodeBase):
    """ class to inherit, for open node classes """

    @abc.abstractmethod
    def setup(self, firmware_path):
        """ Setup the open node with a firmware"""
        pass  # pragma: no cover

    @abc.abstractmethod
    def teardown(self):
        """ Cleanup the open node """
        pass  # pragma: no cover

    @classmethod
    def verify(cls):
        """ Verifiy the open node """
        ret_val = 0
        # Tuple with (class, machine) run 'elftarget.py' on a node firmware
        if (getattr(cls, 'ELF_TARGET', None) is None or
                len(cls.ELF_TARGET) != 2):
            ret_val += 1

        for firmware_attr in ('FW_IDLE', 'FW_AUTOTEST'):
            firmware = getattr(cls, firmware_attr, None)
            if (firmware is not None and not
                    elftarget.is_compatible_with_node(firmware, cls)):
                ret_val += 1

        required_autotest = {'echo', 'get_time'}  # mandatory
        if (getattr(cls, 'AUTOTEST_AVAILABLE', None) is None or
                not required_autotest.issubset(cls.AUTOTEST_AVAILABLE)):
            ret_val += 1

        return ret_val


REGISTRY = {}


# import all the nodes/plugins
def import_all_nodes(pkg_dir):
    """Looks into the given relative path for modules and imports them"""
    pkg_dir = os.path.join(os.path.dirname(__file__), pkg_dir)
    for module_loader, name, _ in pkgutil.iter_modules([pkg_dir]):
        if name in ['tests', 'common']:
            continue
        module = module_loader.find_module(name).load_module(name)
        class_members = inspect.getmembers(module, inspect.isclass)
        for class_member_tuple in class_members:
            class_member_name, class_member = class_member_tuple
            if (not issubclass(
                    class_member, NodeBase) or
                    class_member_name.endswith("Base")):
                continue
            REGISTRY[class_member.TYPE] = class_member


import_all_nodes('open_nodes')
import_all_nodes('control_nodes')


def _node_class(board_type):
    """Return the open node class implementation for `board_type`.

    :raises ValueError: if board class can't be found """
    try:
        output_class = REGISTRY[board_type]
        # Class sanity check
        assert output_class.TYPE == board_type
    except KeyError:
        raise ValueError('Board %s not implemented' % board_type)
    else:
        return output_class


def open_node_class(board_type):
    """Return the open node class implementation for `board_type`.

    :raises ValueError: if board class can't be found """
    output_class = _node_class(board_type)
    if output_class.verify() != 0:
        raise ValueError('Invalid open node class {}'.format(
            output_class.__name__))
    return output_class


def control_node_class(cn_type):
    """Return the control node class implementation for `cn_type`.

    :raises ValueError: if board class can't be found """
    return _node_class(cn_type)


def all_open_nodes_types():
    """Returns all the open nodes classes"""
    return [key for key in REGISTRY
            if issubclass(REGISTRY[key], OpenNodeBase)]


def all_control_nodes_types():
    """Returns all the control nodes classes"""
    return [key for key in REGISTRY
            if issubclass(REGISTRY[key], ControlNodeBase)]
