# -*- coding: utf-8 -*-

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
"""" some tests for the CC2538 wrapper"""

import os
import time
import unittest

import mock

from gateway_code.config import static_path
from gateway_code.open_nodes.node_firefly import NodeFirefly
from .. import cc2538
from ..elftarget import get_elf_load_addr


class TestCC2538(unittest.TestCase):
    """ some tests for the CC2538 wrapper"""

    def test_objdump(self):
        """ test the objdump get_elf_load_addr """
        elf = os.path.abspath(static_path('firefly_autotest.elf'))
        elf_addr = get_elf_load_addr(elf)
        self.assertEqual(0x00200000, elf_addr)
        elf = os.path.abspath(static_path('firefly_idle.elf'))
        elf_addr = get_elf_load_addr(elf)
        self.assertEqual(0x00202000, elf_addr)


@mock.patch('gateway_code.utils.subprocess_timeout.call')
class TestsCC2538Methods(unittest.TestCase):
    """Tests edbg methods."""

    def setUp(self):
        self.cc2538 = cc2538.CC2538({'port': NodeFirefly.TTY,
                                     'baudrate': NodeFirefly.BAUDRATE})

    def test_flash(self, call_mock):
        """Test flash."""
        call_mock.return_value = 0
        ret = self.cc2538.flash(NodeFirefly.FW_IDLE)
        self.assertEqual(0, ret)

        call_mock.return_value = 42
        ret = self.cc2538.flash(NodeFirefly.FW_AUTOTEST)
        # call is called twice and the ret codes are summed up
        self.assertEqual(84, ret)

    def test_reset(self, call_mock):
        """ Test reset"""
        call_mock.return_value = 0
        ret = self.cc2538.reset()
        self.assertEqual(0, ret)

        call_mock.return_value = 42
        ret = self.cc2538.reset()
        self.assertEqual(42, ret)

    def test_invalid_firmware_path(self, _):
        """Test flash an invalid firmware return a non zero value."""
        ret = self.cc2538.flash('/invalid/path')
        assert ret > 0


class TestsCC2538Call(unittest.TestCase):
    # pylint:disable=protected-access
    """ Tests cc2538-bsl call timeout """
    def setUp(self):
        self.timeout = 5
        self.cc2538 = cc2538.CC2538({'port': NodeFirefly.TTY,
                                     'baudrate': NodeFirefly.BAUDRATE},
                                    timeout=self.timeout)
        self.cc2538.args = mock.Mock()

    def test_timeout_call(self):
        """Test timeout reached."""
        self.cc2538.args.return_value = {'args': ['sleep', '10']}
        t_0 = time.time()
        ret = self.cc2538.call_cmd('sleep')
        t_end = time.time()

        # Not to much more
        self.assertLess(t_end - t_0, self.timeout + 1)
        self.assertNotEqual(ret, 0)

    def test_no_timeout(self):
        """Test timeout not reached."""
        self.cc2538.args.return_value = {'args': ['sleep', '1']}
        t_0 = time.time()
        ret = self.cc2538.call_cmd('sleep')
        t_end = time.time()

        # Strictly lower here
        self.assertLess(t_end - t_0, self.timeout - 1)
        self.assertEqual(ret, 0)
