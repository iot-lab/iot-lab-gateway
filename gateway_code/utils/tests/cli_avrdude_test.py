# -*- coding:utf-8 -*-

# pylint: disable=unused-argument
""" Test 'openocd' command line module """

import mock
import unittest

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
        call_mock.return_value = 0
        args = ['avrdude.py', 'flash', 'LEONARDO', '/dev/null']
        with mock.patch('sys.argv', args):
            self.avrdude.flash.return_value = 0
            ret = avrdude.main()
            self.assertEquals(ret, 0)
            self.avrdude.flash.assert_called()

            self.avrdude.flash.return_value = 42
            ret = avrdude.main()
            self.assertEquals(ret, 42)
