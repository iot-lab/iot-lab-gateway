# -*- coding:utf-8 -*-
""" Control Node experiment implementation """

from gateway_code.utils.ftdi_check import ftdi_check
from gateway_code.utils.openocd import OpenOCD
from gateway_code.config import static_path

import logging
LOGGER = logging.getLogger('gateway_code')


class ControlNode(object):
    """ Control Node implemenation """
    TTY = '/dev/ttyCN'
    BAUDRATE = 500000
    OPENOCD_CFG_FILE = static_path('iot-lab-cn.cfg')
    FW_CONTROL_NODE = static_path('control_node.elf')

    def __init__(self):
        self.openocd = OpenOCD(self.OPENOCD_CFG_FILE)

    # def setup(self, firmware_path):
    #     """ Flash Control Node, create serial redirection """
    #     ret_val = 0
    #     ret_val += common.wait_tty(self.TTY, LOGGER, timeout=1)
    #     ret_val += self.g_m.node_flash('m3', firmware_path)
    #     ret_val += self.serial_redirection.start()
    #     return ret_val

    # def teardown(self):
    #     """ Stop serial redirection and flash idle firmware """
    #     ret_val = 0
    #     # cleanup debugger before flashing
    #     ret_val += self.g_m.open_debug_stop()

    #     ret_val += self.serial_redirection.stop()
    #     ret_val += self.g_m.node_flash('m3', config.FIRMWARES['idle'])
    #     return ret_val

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
