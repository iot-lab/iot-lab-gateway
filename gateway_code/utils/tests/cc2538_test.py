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

import unittest

import os

from gateway_code.config import static_path
from gateway_code.utils.elftarget import get_elf_load_addr


class TestCC2538(unittest.TestCase):
    """ some tests for the CC2538 wrapper"""
    def test_objdump(self):
        """ test the objdump get_elf_load_addr """
        elf = os.path.abspath(static_path('firefly_autotest.elf'))
        elf_addr = get_elf_load_addr(elf)
        self.assertEquals(0x00200000, elf_addr)
        elf = os.path.abspath(static_path('idle_firefly.elf'))
        elf_addr = get_elf_load_addr(elf)
        self.assertEquals(0x00202000, elf_addr)
