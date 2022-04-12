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

""" Experiment implementation of an open node that has no node."""
import logging

from gateway_code.common import logger_call
from gateway_code.nodes import OpenNodeBase

LOGGER = logging.getLogger('gateway_code')


class NodeNoBase(OpenNodeBase):
    # pylint:disable=no-member
    """Open node No implementation."""

    @property
    def programmer(self):
        """There's no programmer instance for this type of open node."""
        return None

    @logger_call("Node No: Setup of no node")
    def setup(self, firmware_path=None):
        # pylint:disable=unused-argument,no-self-use
        """.Does nothing."""
        return 0

    @logger_call("Node No: teardown of no node")
    def teardown(self):  # pylint:disable=no-self-use
        """.Does nothing."""
        return 0

    @logger_call("Node No: flash of no node")
    def flash(self, firmware_path=None, binary=False, offset=0):
        # pylint:disable=unused-argument,no-self-use
        """Does nothing."""
        return 0

    @logger_call("Node No: reset of no node")
    def reset(self):  # pylint:disable=no-self-use
        """Does nothing."""
        return 0

    def status(self):
        """Does nothing."""
        return 0

    @classmethod
    def verify(cls):  # pylint:disable=unused-argument
        """This class is always valid."""
        return 0
