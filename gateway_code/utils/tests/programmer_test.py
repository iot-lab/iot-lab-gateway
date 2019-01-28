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

# pylint: disable=no-self-use

""" Test programmer module """

import os
import unittest
import mock

from gateway_code.tests import utils
from gateway_code.utils.cli.programmer import flash, reset, debug


class TestsProgrammer(unittest.TestCase):
    """ Test programmer """

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('m3'))
    @mock.patch('gateway_code.utils.subprocess_timeout.call')
    def test_openocd_method(self, call_mock):
        """ Test openocd method """
        call_mock.return_value = 0
        args = ['programmer.py', '/dev/null']
        with mock.patch('sys.argv', args):
            ret = flash()
            self.assertEqual(ret, 0)

        args2 = ['programmer.py']
        with mock.patch('sys.argv', args2):
            ret = reset()
            self.assertEqual(ret, 0)

        args3 = ['programmer.py', '/path/to/firmware']
        with mock.patch('sys.argv', args3):
            ret = flash()
            self.assertEqual(ret, 1)

        call_mock.return_value = 42
        with mock.patch('sys.argv', args2):
            ret = reset()
            self.assertEqual(ret, 42)

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('m3'))
    @mock.patch('gateway_code.utils.subprocess_timeout.call')
    @mock.patch.dict(os.environ, {'FW': 'xxx'})
    def test_env_flash_failed(self, call_mock):
        """ Test env flash failed"""
        args = ['programmer.py']
        call_mock.return_value = 0
        with mock.patch('sys.argv', args):
            ret = flash()
            self.assertEqual(ret, 1)

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('m3'))
    def test_flash_failed(self):
        """ Test flash failed"""
        args = ['programmer.py']
        with mock.patch('sys.argv', args):
            ret = flash()
            self.assertEqual(ret, -2)

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('m3'))
    @mock.patch('gateway_code.utils.subprocess_timeout.call')
    @mock.patch.dict(os.environ, {'FW': 'autotest'})
    def test_autotest_flash(self, call_mock):
        """ Test autotest flash """
        args = ['programmer.py']
        call_mock.return_value = 0
        with mock.patch('sys.argv', args):
            ret = flash()
            self.assertEqual(ret, 0)

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('m3'))
    @mock.patch('gateway_code.utils.subprocess_timeout.call')
    @mock.patch.dict(os.environ, {'FW': 'idle'})
    def test_idle_flash(self, call_mock):
        """ Test idle flash """
        call_mock.return_value = 0
        args = ['programmer.py']
        with mock.patch('sys.argv', args):
            ret = flash()
            self.assertEqual(ret, 0)

        args2 = ['programmer.py', '/dev/null']
        call_mock.return_value = 0
        with mock.patch('sys.argv', args2):
            ret = flash()
            self.assertEqual(ret, 0)

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('m3'))
    @mock.patch("signal.pause")
    def test_openocd_debug(self, pause_mock):
        """ Test openocd debug """
        args = ['programmer.py']
        pause_mock.side_effect = KeyboardInterrupt
        with mock.patch('sys.argv', args):
            ret = debug()
            self.assertEqual(ret, 0)

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('m3'))
    @mock.patch('gateway_code.utils.openocd.OpenOCD.debug_start')
    def test_openocd_debug_failed(self, debug_mock):
        """ Test openocd debug failed """
        debug_mock.return_value = 1
        args = ['programmer.py']
        with mock.patch('sys.argv', args):
            ret = debug()
            self.assertEqual(ret, 1)

    @mock.patch(utils.READ_CONFIG,
                utils.read_config_mock('m3', control_node_type='iotlab'))
    @mock.patch('gateway_code.utils.subprocess_timeout.call')
    def test_control_node_method(self, call_mock):
        """ Test control node method """
        call_mock.return_value = 0
        args = ['programmer.py', '-cn']
        with mock.patch('sys.argv', args):
            ret = reset()
            self.assertEqual(ret, 0)

        args2 = ['programmer.py', '-cn', '/dev/null']
        with mock.patch('sys.argv', args2):
            ret = flash()
            self.assertEqual(ret, 0)

    @mock.patch(utils.READ_CONFIG,
                utils.read_config_mock('m3', control_node_type='iotlab'))
    @mock.patch.dict(os.environ, {'FW': 'autotest'})
    def test_control_node_autotest(self):
        """ Test control node autotest flash """
        args = ['programmer.py', '-cn']
        with mock.patch('sys.argv', args):
            ret = flash()
            self.assertEqual(ret, -2)

    @mock.patch(utils.READ_CONFIG,
                utils.read_config_mock('m3', control_node_type='no'))
    def test_control_node_detection(self):
        """ Test control node detection """
        args = ['programmer.py', '-cn']
        with mock.patch('sys.argv', args):
            with self.assertRaises(SystemExit):
                flash()

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('leonardo'))
    @mock.patch('gateway_code.utils.avrdude.AvrDude.trigger_bootloader')
    @mock.patch('gateway_code.common.wait_tty')
    @mock.patch('gateway_code.utils.subprocess_timeout.call')
    def test_avrdude_flash(self, call_mock, wait_mock, bootloader_mock):
        """ Test avrdude flash """
        bootloader_mock.return_value = 0
        call_mock.return_value = 0
        wait_mock.return_value = 0
        args = ['programmer.py', '/dev/null']
        with mock.patch('sys.argv', args):
            ret = flash()
            self.assertEqual(ret, 0)

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('leonardo'))
    @mock.patch('gateway_code.utils.avrdude.AvrDude.trigger_bootloader')
    @mock.patch('gateway_code.common.wait_tty')
    def test_avrdude_reset(self, wait_mock, bootloader_mock):
        """ Test avrdude reset """
        bootloader_mock.return_value = 0
        wait_mock.return_value = 0
        args = ['programmer.py']
        with mock.patch('sys.argv', args):
            ret = reset()
            self.assertEqual(ret, 0)

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('leonardo'))
    def test_avrdude_no_method(self):
        """ Test avrdude no method """
        args = ['programmer.py']
        with mock.patch('sys.argv', args):
            ret = debug()
            self.assertEqual(ret, -1)

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('a8'))
    def test_linux_node_no_method(self):
        """ Test Linux node no flash method """
        args = ['programmer.py', '/path/to/firmware']
        with mock.patch('sys.argv', args):
            ret = flash()
            self.assertEqual(ret, -1)

        args2 = ['programmer.py']
        with mock.patch('sys.argv', args2):
            ret = reset()
            self.assertEqual(ret, -1)

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('firefly'))
    @mock.patch('gateway_code.utils.cc2538.CC2538.flash')
    @mock.patch('gateway_code.utils.subprocess_timeout.call')
    def test_cc2538_reset_method(self, call_mock, flash_mock):
        """ Test cc2538 reset method """
        call_mock.return_value = 0
        flash_mock.return_value = 0
        args = ['programmer.py']
        with mock.patch('sys.argv', args):
            ret = reset()
            self.assertEqual(ret, 0)

    @mock.patch(utils.READ_CONFIG,
                utils.read_config_mock('a8', linux_open_node_type='a8_m3'))
    @mock.patch('gateway_code.utils.subprocess_timeout.call')
    def test_linux_open_node_flash(self, call_mock):
        """ Test Linux open node flash """
        args = ['programmer.py', '/dev/null']
        call_mock.return_value = 0
        with mock.patch('sys.argv', args):
            ret = flash()
            self.assertEqual(ret, 0)

    @mock.patch(utils.READ_CONFIG,
                utils.read_config_mock('a8', linux_open_node_type='a8_m3'))
    def test_linux_open_node_no_cn(self):
        """ Test Linux open node without control node"""
        args = ['programmer.py', '-cn']
        with mock.patch('sys.argv', args):
            with self.assertRaises(SystemExit):
                reset()
