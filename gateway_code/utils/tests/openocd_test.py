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


# pylint: disable=missing-docstring
# pylint: disable=too-many-public-methods
# pylint: disable=invalid-name
# pylint: disable=protected-access
# serial mock note correctly detected
# pylint: disable=maybe-no-member

import unittest
import mock

from .. import openocd
from gateway_code.open_nodes.node_m3 import NodeM3  # config file


@mock.patch('subprocess.call')
class TestsMethods(unittest.TestCase):
    """ Tests openocd methods """
    def setUp(self):
        self.ocd = openocd.OpenOCD(NodeM3.OPENOCD_CFG_FILE,
                                   NodeM3.OPENOCD_OPTS)

    def test_flash(self, call_mock):
        """ Test flash """
        call_mock.return_value = 0
        ret = self.ocd.flash(NodeM3.FW_IDLE)
        self.assertEquals(0, ret)

        call_mock.return_value = 42
        ret = self.ocd.flash(NodeM3.FW_IDLE)
        self.assertEquals(42, ret)

    def test_reset(self, call_mock):
        """ Test reset"""
        call_mock.return_value = 0
        ret = self.ocd.reset()
        self.assertEquals(0, ret)

        call_mock.return_value = 42
        ret = self.ocd.reset()
        self.assertEquals(42, ret)

    @mock.patch('subprocess.Popen')
    def test_debug(self, popen_mock, call_mock):
        """Test debug."""
        # Stop without debugging
        ret = self.ocd.debug_stop()
        self.assertEquals(0, ret)

        ret = self.ocd.debug_start()
        self.assertEquals(0, ret)
        self.assertTrue(popen_mock.called)

        # Verify command
        command_list = popen_mock.call_args[1]['args']
        self.assertEqual(len(command_list), 12)
        self.assertEqual(command_list[0], 'openocd')
        self.assertEqual(command_list[-6:],
                         ['-c', 'init', '-c', 'targets', '-c', 'reset halt'])
        # don't test middle args as depends on local path
        popen_mock.reset_mock()

        # Cannot reset or flash
        ret = self.ocd.reset()
        self.assertEqual(ret, 1)
        ret = self.ocd.flash(NodeM3.FW_IDLE)
        self.assertEquals(1, ret)
        # not executed
        self.assertFalse(call_mock.called)

        ret = self.ocd.debug_stop()
        self.assertEquals(0, ret)

    @mock.patch('subprocess.Popen')
    def test_debug_error_stop(self, popen_mock, _):
        """Test error on debug_stop."""
        popen_mock.return_value.terminate.side_effect = OSError()

        self.ocd.debug_start()
        ret = self.ocd.debug_stop()
        self.assertEqual(ret, 1)


class TestsFlashInvalidPaths(unittest.TestCase):
    def test_invalid_config_file_path(self):
        self.assertRaises(IOError, openocd.OpenOCD, '/invalid/path')

    def test_invalid_firmware_path(self):
        ret = openocd.OpenOCD(NodeM3.OPENOCD_CFG_FILE).flash('/invalid/path')
        self.assertNotEqual(0, ret)
