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


# pylint: disable=unused-argument
""" Test 'openocd' command line module """

import unittest
import mock

from ..cli import avrdude


# Command line tests
class TestsAvrDudecli(unittest.TestCase):

    """ Test Avrdude cli """

    def setUp(self):
        avrdude_class = mock.patch(
            'gateway_code.utils.avrdude.AvrDude').start()
        self.avrdude = avrdude_class.return_value

    def tearDown(self):
        mock.patch.stopall()

    @mock.patch('gateway_code.utils.avrdude.AvrDude.trigger_bootloader')
    def test_flash(self, call_mock):
        """ Running command line flash """
        # Instance of 'object' has no 'flash' member"
        # pylint:disable=no-member
        call_mock.return_value = 0
        args = ['avrdude.py', 'flash', 'LEONARDO', '/dev/null']
        with mock.patch('sys.argv', args):
            self.avrdude.flash.return_value = 0
            ret = avrdude.main()
            self.assertEqual(ret, 0)
            self.assertTrue(self.avrdude.flash.called)

            self.avrdude.flash.return_value = 42
            ret = avrdude.main()
            self.assertEqual(ret, 42)
