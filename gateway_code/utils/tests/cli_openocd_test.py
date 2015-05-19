# -*- coding:utf-8 -*-
""" Test 'openocd' command line module """

import mock
import unittest

from ..cli import openocd


# Command line tests
class TestsOpenOCDcli(unittest.TestCase):
    """ Test OpenOCD cli """

    @mock.patch('gateway_code.utils.openocd.flash')
    def test_flash(self, mock_fct):
        """ Running command line flash """

        args = ['openocd.py', 'flash', 'M3', '/dev/null']
        with mock.patch('sys.argv', args):
            mock_fct.return_value = 0
            ret = openocd.main()
            self.assertEquals(ret, 0)

            mock_fct.return_value = 42
            ret = openocd.main()
            self.assertEquals(ret, 42)

    @mock.patch('gateway_code.utils.openocd.reset')
    def test_reset(self, mock_fct):
        """ Running command line reset """
        args = ['openocd.py', 'reset', 'M3']
        with mock.patch('sys.argv', args):
            mock_fct.return_value = 0
            ret = openocd.main()
            self.assertEquals(ret, 0)

            mock_fct.return_value = 42
            ret = openocd.main()
            self.assertEquals(ret, 42)
