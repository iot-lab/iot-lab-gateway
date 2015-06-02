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

    def __init__(self, default_profile):
        self.openocd = OpenOCD(self.OPENOCD_CFG_FILE)
        self.cn_serial = cn_interface.ControlNodeSerial()
        self.protocol = cn_protocol.Protocol(self.cn_serial.send_command)
        self.default_profile = default_profile

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
