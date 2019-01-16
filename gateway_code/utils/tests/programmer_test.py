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
""" Test programmer module """

import unittest
import mock

import gateway_code.utils.programmer

# Command line tests
class TestsProgrammer(unittest.TestCase):
    """ Test programmer """

    def test_flash(self, call_mock):
        """ Test flash """
        call_mock.return_value = 0
        ret = programmer.flash()
        self.assertEqual(0, ret)

        call_mock.return_value = 42
        ret = self.ocd.flash(NodeM3.FW_IDLE)
        self.assertEqual(42, ret)
