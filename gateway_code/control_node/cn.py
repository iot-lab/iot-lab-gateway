# -*- coding:utf-8 -*-
""" Control Node experiment implementation """

import time

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

    def start(self, exp_desc):
        """ Start ControlNode serial interface """
        ret_val = 0
        ret_val += self.reset()
        ret_val += self.cn_serial.start(self.TTY, exp_desc=exp_desc)
        ret_val += self.open_start('dc')
        return ret_val

    def stop(self):
        """ Start ControlNode """
        ret_val = 0
        ret_val += self.open_stop('dc')
        ret_val += self.cn_serial.stop()
        ret_val += self.reset()
        return ret_val

    def start_experiment(self, profile, board_type):
        """ Configure the experiment """
        ret_val = 0
        ret_val += self.protocol.green_led_blink()
        ret_val += self.protocol.set_time()

        #can't be done if we can't use i2C connection
        if(board_type in ('m3', 'a8')):
            ret_val += self.protocol.set_node_id()
        ret_val += self.configure_profile(profile)
        return ret_val

    def stop_experiment(self):
        """ Cleanup the control node configuration
        Also start open node for cleanup """
        ret_val = 0
        ret_val += self.configure_profile(None)
        ret_val += self.open_start('dc')
        ret_val += self.protocol.green_led_on()
        return ret_val

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

    def open_start(self, power=None):
        """ Start open node with 'power' source """
        power = power or self.profile.power
        ret = self.protocol.start_stop('start', power)
        if ret == 0:
            self.open_node_state = 'start'
        return ret

    def open_stop(self, power=None):
        """ Stop open node with 'power' source """
        power = power or self.profile.power
        ret = self.protocol.start_stop('stop', power)
        if ret == 0:
            self.open_node_state = 'stop'
        return ret

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
