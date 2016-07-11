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

""" Control Node experiment implementation """

import time
import logging

from gateway_code.utils.ftdi_check import ftdi_check
from gateway_code.utils.openocd import OpenOCD
from gateway_code.config import static_path
from gateway_code.control_node import cn_interface, cn_protocol

from gateway_code.common import logger_call

LOGGER = logging.getLogger('gateway_code')


class ControlNode(object):
    """ Control Node implemenation """
    ELF_TARGET = ('ELFCLASS32', 'EM_ARM')
    TTY = '/dev/ttyCN'
    BAUDRATE = 500000
    OPENOCD_CFG_FILE = static_path('iot-lab-cn.cfg')
    OPENOCD_OPTS = ('target/stm32f1x.cfg',)
    FW_CONTROL_NODE = static_path('control_node.elf')
    default_profile = None

    def __init__(self, node_id, default_profile):
        self.node_id = node_id
        self.default_profile = default_profile

        self.openocd = OpenOCD.from_node(self)
        self.cn_serial = cn_interface.ControlNodeSerial(self.TTY)
        self.protocol = cn_protocol.Protocol(self.cn_serial.send_command)
        self.open_node_state = 'stop'
        self.profile = self.default_profile

    @logger_call("Control node : Starting of control node serial interface")
    def start(self, exp_id, exp_files=None):
        """ Start ControlNode serial interface """
        ret_val = 0
        ret_val += self.reset()

        oml_cfg = self.cn_serial.oml_xml_config(self.node_id, exp_id,
                                                exp_files)
        ret_val += self.cn_serial.start(oml_cfg)
        ret_val += self.open_start('dc')
        return ret_val

    @logger_call("Control node : Stop control node serial interface")
    def stop(self):
        """ Start ControlNode """
        ret_val = 0
        ret_val += self.open_stop('dc')
        ret_val += self.cn_serial.stop()
        ret_val += self.reset()
        return ret_val

    @logger_call("Control node : Start experiment")
    def start_experiment(self, profile):
        """ Configure the experiment """
        ret_val = 0
        ret_val += self.protocol.green_led_blink()
        ret_val += self.protocol.set_time()
        ret_val += self.protocol.set_node_id(self.node_id)
        ret_val += self.configure_profile(profile)
        return ret_val

    @logger_call("Control node : stop of the experiment")
    def stop_experiment(self):
        """ Cleanup the control node configuration
        Also start open node for cleanup """
        ret_val = 0
        ret_val += self.configure_profile(None)
        ret_val += self.open_start('dc')
        ret_val += self.protocol.green_led_on()
        return ret_val

    @logger_call("Control node : profile configuration")
    def configure_profile(self, profile=None):
        """ Configure the given profile on the control node """
        LOGGER.info('Configure profile on Control Node')
        self.profile = profile or self.default_profile
        ret_val = 0
        # power_mode (start|stop dc|batt)
        ret_val += self.protocol.start_stop(self.open_node_state,
                                            self.profile.power)
        # Monitoring
        ret_val += self.protocol.config_consumption(self.profile.consumption)
        ret_val += self.protocol.config_radio(self.profile.radio)
        ret_val += self.protocol.config_gpio()

        return ret_val

    @logger_call("Control node : start power of open node")
    def open_start(self, power=None):
        """ Start open node with 'power' source """
        power = power or self.profile.power
        ret = self.protocol.start_stop('start', power)
        if ret == 0:
            self.open_node_state = 'start'
        return ret

    @logger_call("Control node : stop power of open node")
    def open_stop(self, power=None):
        """ Stop open node with 'power' source """
        power = power or self.profile.power
        ret = self.protocol.start_stop('stop', power)
        if ret == 0:
            self.open_node_state = 'stop'
        return ret

    @logger_call("Control node : flash the open node")
    def flash(self, firmware_path=None):
        """ Flash the given firmware on Control Node

        :param firmware_path: Path to the firmware to be flashed on `node`.
                              If None, flash 'control_node' firmware
        """
        firmware_path = firmware_path or self.FW_CONTROL_NODE
        LOGGER.info('Flash firmware on Control Node %s', firmware_path)
        ret = self.openocd.flash(firmware_path)
        self._wait_control_node_ready()
        return ret

    @logger_call("Control node : reset")
    def reset(self):
        """ Reset the Control Node using jtag """
        LOGGER.info('Reset Control Node')
        ret = self.openocd.reset()
        self._wait_control_node_ready()
        return ret

    @staticmethod
    def _wait_control_node_ready():
        """ Wait that the ControlNode firmware starts.

        It waits one second when starting, and may also trigger udev when
        restarting a node. This take a bit more than 1.1 second.
        So wait 2 seconds to be safe.  """
        time.sleep(2)

    @staticmethod
    def status():
        """ Check Control node status """
        return ftdi_check('control', '4232')
