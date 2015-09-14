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


""" Test gateway_code.open_node module """

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=too-many-public-methods

import unittest
from mock import patch

from gateway_code.open_nodes.node_a8 import NodeA8


class TestNodeA8(unittest.TestCase):

    @patch('gateway_code.open_nodes.node_a8.SerialExpectForSocket')
    def test__debug_boot_thread(self, expect_class):
        """ Run both cases for coverage """
        serial_expect = expect_class.return_value

        a8_node = NodeA8()

        serial_expect.expect.return_value = ''
        ret = a8_node.wait_booted(0)
        self.assertEquals(ret, '')

        serial_expect.expect.return_value = ' login: '
        ret = a8_node.wait_booted(0)
        self.assertIn('login:', ret)

    @staticmethod
    def test_error_cases():
        """ Coverage cases execution """
        a8_node = NodeA8()
        a8_node._debug_boot_stop()
