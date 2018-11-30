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

""" tests for utils/tools FlashTool """

import time
import unittest

from mock import mock

from gateway_code.utils.tools import FlashTool


class TestsCall(unittest.TestCase):
    """ Tests FlashTool call timeout """
    def setUp(self):
        self.timeout = 5
        self.tool = FlashTool(timeout=self.timeout)
        self.tool.args = mock.Mock()

    def test_timeout_call(self):
        """Test timeout reached."""
        self.tool.args.return_value = {'args': ['sleep', '10']}
        t_0 = time.time()
        ret = self.tool.call_cmd('sleep')
        t_end = time.time()

        # Not to much more
        self.assertLess(t_end - t_0, self.timeout + 1)
        self.assertNotEquals(ret, 0)

    def test_no_timeout(self):
        """Test timeout not reached."""
        self.tool.args.return_value = {'args': ['sleep', '1']}
        t_0 = time.time()
        ret = self.tool.call_cmd('sleep')
        t_end = time.time()

        # Strictly lower here
        self.assertLess(t_end - t_0, self.timeout - 1)
        self.assertEquals(ret, 0)
