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

""" gateway_code.control_node (iotlab) unit tests files """

import unittest
from mock import Mock, patch, call

from gateway_code.nodes import ControlNodeBase, import_all_nodes
from gateway_code.control_nodes.cn_iotlab import ControlNodeIotlab


class TestCnIotlab(unittest.TestCase):
    """Unittest class for iotlab control node."""

    def setUp(self):
        self.cn_node = ControlNodeIotlab('test', None)
        assert self.cn_node.open_node_state == 'stop'
        self.cn_node.default_profile = Mock()
        self.cn_node.default_profile.power = 'test_power'
        self.cn_node.default_profile.consumption = 'test_consumption'
        self.cn_node.default_profile.radio = 'test_radio'
        cn_serial_class = patch('gateway_code.control_nodes.cn_iotlab.'
                                'cn_interface.ControlNodeSerial').start()
        self.cn_node.cn_serial = cn_serial_class.return_value
        self.cn_node.cn_serial.oml_xml_config.return_value = 'oml_cfg_test'
        self.cn_node.cn_serial.start.return_value = 0
        self.cn_node.cn_serial.stop.return_value = 0

        cn_protocol_class = patch('gateway_code.control_nodes.cn_iotlab.'
                                  'cn_interface.ControlNodeSerial').start()
        self.cn_node.protocol = cn_protocol_class.return_value
        self.cn_node.protocol.start_stop.return_value = 0
        self.cn_node.protocol.green_led_blink.return_value = 0
        self.cn_node.protocol.green_led_on.return_value = 0
        self.cn_node.protocol.set_time.return_value = 0
        self.cn_node.protocol.set_node_id.return_value = 0
        self.cn_node.protocol.config_consumption.return_value = 0
        self.cn_node.protocol.config_radio.return_value = 0

        openocd_class = patch('gateway_code.utils.openocd.OpenOCD').start()
        self.cn_node.openocd = openocd_class.return_value
        self.cn_node.openocd.flash.return_value = 0
        self.cn_node.openocd.reset.return_value = 0

        # Let's be fast
        patch('time.sleep').start()

    def tearDown(self):
        patch.stopall()

    @classmethod
    def tearDownClass(cls):
        # Mocking some features of the control node has side effects on
        # following tests. We need to explicitly clear ControlNodeBase registry
        # at the end of all unit tests and reimport the available control
        # nodes.
        del ControlNodeBase.__registry__[ControlNodeIotlab.TYPE]
        import_all_nodes('control_nodes')

    def test_start(self):
        """Test start of iotlab control node."""
        self.cn_node.protocol.start_stop.return_value = 1
        assert self.cn_node.start('123') == 1
        assert self.cn_node.open_node_state == 'stop'
        self.cn_node.cn_serial.oml_xml_config.assert_called_once()
        self.cn_node.cn_serial.start.assert_called_once()
        self.cn_node.protocol.start_stop.return_value = 0
        self.cn_node.protocol.start_stop.call_count = 0
        self.cn_node.cn_serial.oml_xml_config.call_count = 0
        self.cn_node.cn_serial.start.call_count = 0

        assert self.cn_node.start('123') == 0
        self.cn_node.cn_serial.oml_xml_config.assert_called_once()
        self.cn_node.cn_serial.oml_xml_config.assert_called_with(
            'test', '123', None)
        self.cn_node.cn_serial.start.assert_called_once()
        self.cn_node.cn_serial.start.assert_called_with('oml_cfg_test')
        self.cn_node.protocol.start_stop.assert_called_once()
        self.cn_node.protocol.start_stop.assert_called_with('start', 'dc')
        assert self.cn_node.open_node_state == 'start'

    def test_setup(self):
        """Test setup of iotlab control node."""
        assert self.cn_node.setup() == 0
        assert self.cn_node.openocd.flash.call_count == 1
        self.cn_node.openocd.flash.assert_called_with(
            ControlNodeIotlab.FW_CONTROL_NODE)

    def test_stop(self):
        """Test stop of iotlab control node."""
        assert self.cn_node.stop() == 0
        self.cn_node.cn_serial.stop.assert_called_once()
        self.cn_node.protocol.start_stop.assert_called_once()
        self.cn_node.protocol.start_stop.assert_called_with('stop', 'dc')
        assert self.cn_node.open_node_state == 'stop'

        assert self.cn_node.start('123') == 0
        assert self.cn_node.open_node_state == 'start'
        self.cn_node.protocol.start_stop.return_value = 1
        assert self.cn_node.stop() == 1
        assert self.cn_node.open_node_state == 'start'

    def test_start_experiment(self):
        """Test start experiment of iotlab control node."""
        assert self.cn_node.start_experiment(None) == 0
        self.cn_node.protocol.green_led_blink.assert_called_once()
        self.cn_node.protocol.set_time.assert_called_once()
        self.cn_node.protocol.set_node_id.assert_called_once()
        self.cn_node.protocol.set_node_id.assert_called_with('test')
        self.cn_node.protocol.config_consumption.assert_called_once()
        self.cn_node.protocol.config_consumption.assert_called_with(
            'test_consumption')
        self.cn_node.protocol.config_radio.assert_called_once()
        self.cn_node.protocol.config_radio.assert_called_with(
            'test_radio')
        self.cn_node.protocol.start_stop.assert_called_once()
        self.cn_node.protocol.start_stop.assert_called_with(
            'stop', 'test_power')

    def test_stop_experiment(self):
        """Test stop experiment of iotlab control node."""
        assert self.cn_node.stop_experiment() == 0
        self.cn_node.protocol.green_led_on.assert_called_once()
        assert self.cn_node.protocol.start_stop.call_count == 2
        assert self.cn_node.protocol.start_stop.call_args_list == \
            [call('stop', 'test_power'), call('start', 'dc')]

        self.cn_node.protocol.config_consumption.assert_called_once()
        self.cn_node.protocol.config_consumption.assert_called_with(
            'test_consumption')
        self.cn_node.protocol.config_radio.assert_called_once()
        self.cn_node.protocol.config_radio.assert_called_with(
            'test_radio')

    def test_autotest_setup(self):
        """Test autotest setup of iotlab control node."""
        assert self.cn_node.autotest_setup(None) == 0
        self.cn_node.cn_serial.start.assert_called_once()
        self.cn_node.cn_serial.start.assert_called_with()
        self.cn_node.protocol.set_time.assert_called_once()

    def test_autotest_teardown(self):
        """Test autotest setup of iotlab control node."""
        assert self.cn_node.autotest_teardown(False) == 0
        self.cn_node.cn_serial.stop.assert_called_once()
        assert self.cn_node.protocol.start_stop.call_count == 0

        assert self.cn_node.autotest_teardown(True) == 0
        assert self.cn_node.cn_serial.stop.call_count == 2
        self.cn_node.protocol.start_stop.assert_called_once()
        self.cn_node.protocol.start_stop.assert_called_with('stop', 'dc')

    def test_status(self):
        """Test status method of iotlab control node."""
        with patch('gateway_code.utils.ftdi_check.ftdi_check') as ftdi_check:
            ftdi_check.return_value = 42
            assert self.cn_node.status() == 42
            ftdi_check.assert_called_with('control', '4232')
