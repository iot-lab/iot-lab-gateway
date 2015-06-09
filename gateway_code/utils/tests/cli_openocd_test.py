# -*- coding:utf-8 -*-
""" Test 'openocd' command line module """

import mock
import unittest

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

        args = ['openocd.py', 'flash', 'M3', '/dev/null']
        with mock.patch('sys.argv', args):
            self.ocd.flash.return_value = 0
            ret = openocd.main()
            self.assertEquals(ret, 0)
            self.ocd.flash.assert_called()

            self.ocd.flash.return_value = 42
            ret = openocd.main()
            self.assertEquals(ret, 42)

    def test_reset(self):
        """ Running command line reset """
        args = ['openocd.py', 'reset', 'M3']
        with mock.patch('sys.argv', args):
            self.ocd.reset.return_value = 0
            ret = openocd.main()
            self.assertEquals(ret, 0)
            self.ocd.reset.assert_called()

            self.ocd.reset.return_value = 42
            ret = openocd.main()
            self.assertEquals(ret, 42)
