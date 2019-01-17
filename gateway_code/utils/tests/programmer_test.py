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

import unittest
import mock
import pytest

from gateway_code.tests import utils
from gateway_code.utils.cli.programmer import flash, reset, debug


class TestsProgrammer(unittest.TestCase):
    """ Test programmer """

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('m3'))
    @mock.patch('gateway_code.utils.subprocess_timeout.call')
    def test_openocd_flash(self, call_mock):
        """ Test openocd flash """
        args = ['programmer.py', '/dev/null']
        call_mock.return_value = 0
        with mock.patch('sys.argv', args):
            ret = flash()
            self.assertEqual(0, ret)

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('m3'))
    @mock.patch('gateway_code.utils.subprocess_timeout.call')
    def test_openocd_reset(self, call_mock):
        """ Test openocd reset """
        args = ['programmer.py']
        call_mock.return_value = 0
        with mock.patch('sys.argv', args):
            ret = reset()
            self.assertEqual(0, ret)

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('m3'))
    @mock.patch('gateway_code.utils.subprocess_timeout.call')
    def test_openocd_reset_failed(self, call_mock):
        """ Test openocd reset """
        args = ['programmer.py']
        call_mock.return_value = 42
        with mock.patch('sys.argv', args):
            ret = reset()
            self.assertEqual(42, ret)

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('m3'))
    @mock.patch("signal.pause")
    def test_openocd_debug(self, pause_mock):
        """ Test openocd debug """
        args = ['programmer.py']
        pause_mock.side_effect = KeyboardInterrupt
        with mock.patch('sys.argv', args):
            ret = debug()
            self.assertEqual(0, ret)

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('m3'))
    @mock.patch('gateway_code.utils.openocd.OpenOCD.debug_start')
    def test_openocd_debug_failed(self, debug_mock):
        """ Test openocd debug failed """
        args = ['programmer.py']
        debug_mock.return_value = 1
        with mock.patch('sys.argv', args):
            ret = debug()
            self.assertEqual(1, ret)

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
            self.assertEqual(0, ret)

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
            self.assertEqual(0, ret)

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('leonardo'))
    def test_avrdude_no_method(self):
        """ Test avrdude no method """
        args = ['programmer.py']
        with mock.patch('sys.argv', args):
            with pytest.raises(ValueError):
                debug()

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('a8'))
    def test_linux_node_no_flash_method(self):
        """ Test Linux node no flash method """
        args = ['programmer.py', '/path/to/firmware']
        with mock.patch('sys.argv', args):
            with pytest.raises(ValueError):
                flash()

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('a8'))
    def test_linux_node_no_reset_method(self):
        """ Test Linux node no reset method """
        args = ['programmer.py']
        with mock.patch('sys.argv', args):
            with pytest.raises(ValueError):
                reset()

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
            self.assertEqual(0, ret)

    @mock.patch(utils.READ_CONFIG,
                utils.read_config_mock('m3', control_node_type='iotlab'))
    @mock.patch('gateway_code.utils.subprocess_timeout.call')
    def test_control_node_openocd_flash(self, call_mock):
        """ Test control node openocd flash """
        args = ['programmer.py', '-cn', '/dev/null']
        call_mock.return_value = 0
        with mock.patch('sys.argv', args):
            ret = flash()
            self.assertEqual(0, ret)
