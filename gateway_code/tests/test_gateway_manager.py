#! /usr/bin/env python

"""
Unit tests for gateway-manager
Complement the 'integration' tests
"""

import unittest
import mock

from gateway_code import gateway_manager
from gateway_code import config

class TestA8StartStop(unittest.TestCase):

    def test_setup(self):
        """ Test running gateway_manager with setup without error """

        g_m = gateway_manager.GatewayManager()
        g_m.node_flash = mock.Mock(return_value=0)
        try:
            g_m.setup()
        except StandardError:
            self.fail("Should not raise an exception during setup")

    def test_setup_fail_flash(self):
        """ Run setup with a flash fail error """
        g_m = gateway_manager.GatewayManager()
        g_m.node_flash = mock.Mock(return_value=1)
        self.assertRaises(StandardError, g_m.setup)

    def test_start_stop_a8_tty(self):
        """ Test running _debug_start_a8_tty and _debyg_stop_a8_tty fcs """
        g_m = gateway_manager.GatewayManager()

        self.assertEquals(0, g_m._debug_start_a8_tty('/dev/null'))
        self.assertNotEquals(0, g_m._debug_start_a8_tty('no_tty_file'))

        self.assertNotEquals(0, g_m._debug_stop_a8_tty('/dev/null'))
        self.assertEquals(0, g_m._debug_stop_a8_tty('no_tty_file'))
