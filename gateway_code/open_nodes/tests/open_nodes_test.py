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
"""open_nodes package tests """


from __future__ import print_function

import pytest

from mock import patch

from gateway_code.nodes import (open_node_class, control_node_class,
                                all_open_nodes_types, all_control_nodes_types,
                                OpenNodeBase, ControlNodeBase, REGISTRY)
from gateway_code.open_nodes.node_a8 import NodeA8
from gateway_code.open_nodes.node_m3 import NodeM3


def test_node_class():
    """Test loading essential open node classes."""
    assert NodeM3.__name__ == open_node_class('m3').__name__
    assert NodeA8.__name__ == open_node_class('a8').__name__


def test_open_node_class_errors():
    """Test error while loading an open node class."""
    # No module
    with pytest.raises(ValueError, match='^Board unknown not implemented*$'):
        open_node_class('unknown')


@patch('subprocess.check_output')
def test_nodes_classes(check_output):
    """Test loading all implemented open nodes implementation."""
    # node_lora_gateway starts the lora_pkt_forwarder during initialization
    # so we need to mock the process pid check.
    check_output.return_value = 42
    for node in all_open_nodes_types():
        # No exception
        print(node)
        node_class = open_node_class(node)
        node_class()
        print(node_class)


def test_missing_overrides():
    """
    Test that a Node that doesnt implement the mandatory
    methods can't be instantiated
    """

    # pylint: disable=abstract-method
    class MyNode(OpenNodeBase):
        """methods purposefully not implemented"""

    # trying to instantiate it raises TypeError
    pytest.raises(TypeError, MyNode.__init__)


def test_registry_open_node():
    """ Verify the open node registry metaclass """
    class MyNode(OpenNodeBase):
        # pylint:disable=abstract-method
        """Basic empty OpenNode"""
        TYPE = "my_node"
        ELF_TARGET = ('ELFCLASS32', 'EM_ARM')
        AUTOTEST_AVAILABLE = ['echo', 'get_time']

    REGISTRY[MyNode.TYPE] = MyNode

    assert open_node_class("my_node") == MyNode

    with pytest.raises(ValueError):
        open_node_class("invalid_node")

    del REGISTRY[MyNode.TYPE]


def test_registry_control_node():
    """ Verify the control node registry metaclass """
    class MyControlNode(ControlNodeBase):
        # pylint:disable=abstract-method
        """Basic empty ControlNode"""
        TYPE = "my_control_node"
        ELF_TARGET = ('ELFCLASS32', 'EM_ARM')

    REGISTRY[MyControlNode.TYPE] = MyControlNode

    assert control_node_class("my_control_node") == MyControlNode

    assert "my_control_node" in all_control_nodes_types()

    with pytest.raises(ValueError):
        control_node_class("invalid_node")

    del REGISTRY[MyControlNode.TYPE]


# parent class no TYPE
class BaseOpenNode(OpenNodeBase):
    """parent class with no TYPE attribute"""
    TYPE = "base_open_node"
    ELF_TARGET = ('ELFCLASS32', 'EM_ARM')
    AUTOTEST_AVAILABLE = ['echo', 'get_time']
    TTY = '/dev/iotlab/tty_stlink'
    BAUDRATE = 4242

    @property
    def programmer(self):
        return None

    def setup(self, firmware_path):
        print(f"setup base open node with {firmware_path}")
        return 42

    def teardown(self):
        return 4242

    def status(self):
        return 0


def test_registry_inheritance():
    """ test case for open node that derive from other open nodes """

    class DerivedOpenNode(BaseOpenNode):
        # pylint:disable=abstract-method
        """Derivation with normal class inheritance"""
        TYPE = "derived_open_node"

    class MixinDerivedOpenNode(BaseOpenNode, OpenNodeBase):
        # pylint:disable=abstract-method
        """Derivation + OpenNode mixin"""
        TYPE = "mixin_derived_open_node"

    REGISTRY[BaseOpenNode.TYPE] = BaseOpenNode
    REGISTRY[DerivedOpenNode.TYPE] = DerivedOpenNode
    REGISTRY[MixinDerivedOpenNode.TYPE] = MixinDerivedOpenNode

    assert open_node_class("base_open_node") == BaseOpenNode
    assert open_node_class("derived_open_node") == DerivedOpenNode
    assert open_node_class("mixin_derived_open_node") == MixinDerivedOpenNode

    del REGISTRY[BaseOpenNode.TYPE]
    del REGISTRY[DerivedOpenNode.TYPE]
    del REGISTRY[MixinDerivedOpenNode.TYPE]


def test_open_node_inheritance():
    """
        test case for open node that derive from other open nodes
        in the case the superclass does not have the TYPE attribute
    """

    class NodeStLinkBoard1(BaseOpenNode):
        """derived class 1"""
        TYPE = "stlink_board_1"

    class NodeStLinkBoard2(BaseOpenNode, OpenNodeBase):
        """derived class 2"""
        TYPE = "stlink_board_2"

    REGISTRY[NodeStLinkBoard1.TYPE] = NodeStLinkBoard1
    REGISTRY[NodeStLinkBoard2.TYPE] = NodeStLinkBoard2

    board_1 = open_node_class("stlink_board_1")
    board_2 = open_node_class("stlink_board_2")

    for node in all_open_nodes_types():
        assert open_node_class(node) != BaseOpenNode

    assert board_1 == NodeStLinkBoard1
    assert board_2 == NodeStLinkBoard2

    board_instance = board_1()

    assert board_instance.TTY == '/dev/iotlab/tty_stlink'
    assert board_instance.BAUDRATE == 4242

    assert board_instance.setup('path/to/firmware') == 42
    assert board_instance.teardown() == 4242
    assert board_instance.status() == 0
    assert board_instance.programmer is None

    del REGISTRY[NodeStLinkBoard1.TYPE]
    del REGISTRY[NodeStLinkBoard2.TYPE]


def test_node_verify_errors():
    """test case for verify open node method."""

    class OpenNodeElfTargetInvalid(BaseOpenNode):
        # pylint:disable=abstract-method,unused-variable
        """OpenNode with invalid elf target attribute."""
        TYPE = "open_node_elf_target_invalid"
        ELF_TARGET = ('INVALID')

    REGISTRY[OpenNodeElfTargetInvalid.TYPE] = OpenNodeElfTargetInvalid

    with pytest.raises(ValueError):
        open_node_class("open_node_elf_target_invalid")

    # Remove test node from registry
    del REGISTRY[OpenNodeElfTargetInvalid.TYPE]

    class OpenNodeNoElfTargetNone(BaseOpenNode):
        # pylint:disable=abstract-method,unused-variable
        """OpenNode with None elf target attribute."""
        TYPE = "open_node_elf_target_none"
        ELF_TARGET = None

    REGISTRY[OpenNodeNoElfTargetNone.TYPE] = OpenNodeNoElfTargetNone

    with pytest.raises(ValueError):
        open_node_class("open_node_elf_target_none")

    # Remove test node from registry
    del REGISTRY[OpenNodeNoElfTargetNone.TYPE]

    class OpenNodeInvalidAutotest(BaseOpenNode):
        # pylint:disable=abstract-method,unused-variable
        """OpenNode with invalid autotest attribute."""
        TYPE = "open_node_invalid_autotest"
        AUTOTEST_AVAILABLE = ['echo', 'invalid']

    REGISTRY[OpenNodeInvalidAutotest.TYPE] = OpenNodeInvalidAutotest

    with pytest.raises(ValueError):
        open_node_class("open_node_invalid_autotest")

    # Remove test node from registry
    del REGISTRY[OpenNodeInvalidAutotest.TYPE]

    class OpenNodeIncompatibleElf(BaseOpenNode):
        # pylint:disable=abstract-method,unused-variable
        """OpenNode with incompatible firmwares."""
        TYPE = "open_node_incompatible_elf"
        FW_IDLE = "idle"
        FW_AUTOTEST = "autotest"

    REGISTRY[OpenNodeIncompatibleElf.TYPE] = OpenNodeIncompatibleElf

    with patch('gateway_code.utils.'
               'elftarget.is_compatible_with_node') as is_compatible:
        is_compatible.return_value = False
        with pytest.raises(ValueError):
            open_node_class("open_node_incompatible_elf")

    # Remove test node from registry
    del REGISTRY[OpenNodeIncompatibleElf.TYPE]
