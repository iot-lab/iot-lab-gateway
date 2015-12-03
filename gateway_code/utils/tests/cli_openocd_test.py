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

""" Test 'openocd' command line module """

import unittest
import mock

from ..cli import openocd


# Command line tests
class TestsOpenOCDcli(unittest.TestCase):
    """ Test OpenOCD cli """
    def setUp(self):
        ocd_class = mock.patch('gateway_code.utils.openocd.OpenOCD').start()
        self.ocd = ocd_class.return_value

    def tearDown(self):
        mock.patch.stopall()

    def test_flash(self):
        """ Running command line flash """
        # Instance of 'object' has no 'flash' member"
        # pylint:disable=no-member

        args = ['openocd.py', 'flash', 'M3', '/dev/null']
        with mock.patch('sys.argv', args):
            self.ocd.flash.return_value = 0
            ret = openocd.main()
            self.assertEquals(ret, 0)
            self.assertTrue(self.ocd.flash.called)

            self.ocd.flash.return_value = 42
            ret = openocd.main()
            self.assertEquals(ret, 42)

    def test_reset(self):
        """ Running command line reset """
        # Instance of 'object' has no 'flash' member"
        # pylint:disable=no-member

        args = ['openocd.py', 'reset', 'M3']
        with mock.patch('sys.argv', args):
            self.ocd.reset.return_value = 0
            ret = openocd.main()
            self.assertEquals(ret, 0)
            self.assertTrue(self.ocd.reset.called)

            self.ocd.reset.return_value = 42
            ret = openocd.main()
            self.assertEquals(ret, 42)
