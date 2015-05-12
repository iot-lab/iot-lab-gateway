# -*- coding:utf-8 -*-
""" Control Node experiment implementation """

from gateway_code import openocd_cmd

import logging
LOGGER = logging.getLogger('gateway_code')


class ControlNode(object):
    """ Control Node implemenation """
    tty = '/dev/ttyCN'
    baudrate = 500000
    openocd_cfg_file = 'iot-lab-cn.cfg'

    def __init__(self):
        pass

    # def setup(self, firmware_path):
    #     """ Flash Control Node, create serial redirection """
    #     ret_val = 0
    #     ret_val += common.wait_tty(self.tty, LOGGER, timeout=1)
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

    @staticmethod
    def flash(firmware_path):
        """ Flash the given firmware on Control Node
        :param firmware_path: Path to the firmware to be flashed on `node`.
        """
        LOGGER.debug('Flash firmware on Control Node %s', firmware_path)
        return openocd_cmd.flash('gwt', firmware_path)

    @staticmethod
    def reset():
        """ Reset the Control Node using jtag """
        LOGGER.info('Reset Control Node')
        return openocd_cmd.reset('gwt')
