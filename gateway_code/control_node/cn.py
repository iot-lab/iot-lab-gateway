# -*- coding:utf-8 -*-
""" Control Node experiment implementation """

from gateway_code.utils.ftdi_check import ftdi_check
from gateway_code.utils.openocd import OpenOCD
from gateway_code.config import static_path
from gateway_code.control_node import cn_interface, cn_protocol

import logging
LOGGER = logging.getLogger('gateway_code')


class ControlNode(object):
    """ Control Node implemenation """
    TTY = '/dev/ttyCN'
    BAUDRATE = 500000
    OPENOCD_CFG_FILE = static_path('iot-lab-cn.cfg')
    FW_CONTROL_NODE = static_path('control_node.elf')
    default_profile = None

    def __init__(self, default_profile):
        self.default_profile = default_profile

        self.openocd = OpenOCD(self.OPENOCD_CFG_FILE)
        self.cn_serial = cn_interface.ControlNodeSerial()
        self.protocol = cn_protocol.Protocol(self.cn_serial.send_command)
        self.open_node_state = 'stop'
        self.profile = self.default_profile

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
        return ret_val

    def flash(self, firmware_path=None):
        """ Flash the given firmware on Control Node
        :param firmware_path: Path to the firmware to be flashed on `node`.
            If None, flash 'control_node' firmware
        """
        firmware_path = firmware_path or self.FW_CONTROL_NODE
        LOGGER.info('Flash firmware on Control Node %s', firmware_path)
        return self.openocd.flash(firmware_path)

    def reset(self):
        """ Reset the Control Node using jtag """
        LOGGER.info('Reset Control Node')
        return self.openocd.reset()

    @staticmethod
    def status():
        """ Check Control node status """
        return ftdi_check('control', '4232')
