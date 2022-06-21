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


# pylint: disable=missing-docstring
# pylint: disable=too-many-public-methods
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=maybe-no-member
# pylint: disable=unused-argument

import time
import unittest

import mock

from gateway_code.open_nodes.node_openmoteb import NodeOpenmoteb
from .. import segger


class TestsMethods(unittest.TestCase):
    """Tests segger methods."""

    def setUp(self):
        self.segger = segger.Segger.from_node(NodeOpenmoteb)

    @mock.patch('gateway_code.utils.subprocess_timeout.call')
    def test_flash(self, call_mock):
        """Test flash."""
        call_mock.return_value = 0
        ret = self.segger.flash(NodeOpenmoteb.FW_IDLE)
        self.assertEqual(0, ret)

        call_mock.return_value = 42
        ret = self.segger.flash(NodeOpenmoteb.FW_AUTOTEST)
        # call is called twice and the ret codes are summed up
        self.assertEqual(84, ret)

    def test_invalid_firmware_path(self):
        ret = self.segger.flash('/invalid/path')
        self.assertNotEqual(0, ret)


class TestsCall(unittest.TestCase):
    """ Tests segger call timeout """
    def setUp(self):
        self.timeout = 5
        self.segger = segger.Segger.from_node(NodeOpenmoteb,
                                              timeout=self.timeout)
        self.segger._segger_args_jlinkexe = mock.Mock()

    def test_timeout_call(self):
        """Test timeout reached."""
        self.segger._segger_args_jlinkexe.return_value = \
            {'args': ['sleep', '10']}
        t_0 = time.time()
        ret = self.segger._call_cmd_flash('sleep')
        t_end = time.time()

        # Not to much more
        self.assertLess(t_end - t_0, self.timeout + 1)
        self.assertNotEqual(ret, 0)

    def test_no_timeout(self):
        """Test timeout not reached."""
        self.segger._segger_args_jlinkexe.return_value = \
            {'args': ['sleep', '1']}
        t_0 = time.time()
        ret = self.segger._call_cmd_flash('sleep')
        t_end = time.time()

        # Strictly lower here
        self.assertLess(t_end - t_0, self.timeout - 1)
        self.assertEqual(ret, 0)
