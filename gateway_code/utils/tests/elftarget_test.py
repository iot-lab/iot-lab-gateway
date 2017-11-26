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

"""Test utils.elftarget."""

import os
import logging
import unittest
import runpy
from cStringIO import StringIO

import mock
from testfixtures import LogCapture

from .. import elftarget

FIRMWARES_DIR = os.path.join(os.path.dirname(__file__), 'elftarget_firmwares')


def firmware(name):
    """Return test firmware path."""
    return os.path.join(FIRMWARES_DIR, name)


class TestElfTarget(unittest.TestCase):
    """Test elftarget.elf_target module."""

    def test_elf_target_valid(self):
        """Test valid elf targets."""
        target = elftarget.elf_target(firmware('m3_idle.elf'))
        self.assertEqual(target, ('ELFCLASS32', 'EM_ARM'))
        target = elftarget.elf_target(firmware('leonardo_idle.elf'))
        self.assertEqual(target, ('ELFCLASS32', 'EM_AVR'))

    def test_invalid_elf(self):
        """Test invalid elf files or non elf files."""
        # elf relocation file
        self.assertRaisesRegexp(
            ValueError, 'Not an executable elf file: ET_REL',
            elftarget.elf_target, firmware('idle.c.o'))
        # wsn430 firmware
        self.assertRaisesRegexp(
            ValueError, 'Not a valid elf file',
            elftarget.elf_target, firmware('wsn430_print_uids.hex'))


class TestElfTargetIsCompatibleWithNode(unittest.TestCase):
    """Test elftarget.is_compatible_with_node."""

    def setUp(self):
        self.m3_class = mock.Mock()
        self.m3_class.ELF_TARGET = ('ELFCLASS32', 'EM_ARM')
        self.log = LogCapture('gateway_code', level=logging.DEBUG)

    def tearDown(self):
        self.log.uninstall()

    def test_m3_like_elf_check(self):
        """Test elftarget for an m3 like node."""
        ret = elftarget.is_compatible_with_node(firmware('m3_idle.elf'),
                                                self.m3_class)
        self.assertTrue(ret)
        self.log.check()

        # invalid target
        ret = elftarget.is_compatible_with_node(firmware('node.z1'),
                                                self.m3_class)
        self.assertFalse(ret)
        self.log.check()

        # invalid, not elf file
        ret = elftarget.is_compatible_with_node(
            firmware('wsn430_print_uids.hex'), self.m3_class)
        self.assertFalse(ret)
        self.log.check(('gateway_code', 'WARNING',
                        'Invalid firmware: Not a valid elf file'))


class TestElftargetMain(unittest.TestCase):
    """Test running elftarget script."""

    def test_main(self):
        """Test running script."""
        argv = ['elftarget.py', firmware('m3_idle.elf')]
        stdout = StringIO()
        stderr = StringIO()

        script = os.path.join(os.path.dirname(__file__), '..', 'elftarget.py')
        with mock.patch('sys.stderr', stderr):
            with mock.patch('sys.stdout', stdout):
                with mock.patch('sys.argv', argv):
                    runpy.run_path(script, run_name='__main__')

        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(stdout.getvalue(), "('ELFCLASS32', 'EM_ARM')\n")
