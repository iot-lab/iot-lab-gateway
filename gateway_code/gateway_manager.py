#! /usr/bin/env python
# -*- coding:utf-8 -*-


"""
manager script
"""

from gateway_code import config
from gateway_code import openocd_cmd
from gateway_code.profile import Profile
from gateway_code.serial_redirection import SerialRedirection
from gateway_code.autotest import autotest

from gateway_code import control_node_interface, protocol_cn

import time

import gateway_code.gateway_logging
import logging


LOGGER = logging.getLogger('gateway_code')


# Disable: I0011 - 'locally disabling warning'
# too many instance attributes
# pylint:disable=I0011,R0902
class GatewayManager(object):
    """
    Gateway Manager class,

    Manages experiments, open node and control node
    """

    def __init__(self, log_folder='.'):

        # current experiment infos
        self.exp_id = None
        self.user = None
        self.experiment_is_running = False
        self.profile = None
        self.open_node_state = "stop"

        gateway_code.gateway_logging.init_logger(log_folder)  # logger config

        self.cn_serial = control_node_interface.ControlNodeSerial()
        self.protocol = protocol_cn.Protocol(self.cn_serial.send_command)

        # open node interraction
        self.serial_redirection = SerialRedirection('m3')

    def setup(self):
        """ Run commands that might crash
        Must be run before running other commands """
        # Setup control node
        ret = self.node_flash('gwt', config.FIRMWARES['control_node'])
        if ret != 0:
            raise StandardError("Control node flash failed: {ret:%d, '%s')",
                                ret, config.FIRMWARES['control_node'])

    def exp_start(self, exp_id, user,
                  firmware_path=None, profile=None):
        """
        Start an experiment

        :param exp_id: experiment id
        :param user: user owning the experiment
        :param firmware_path: path of the firmware file to flash
        :param profile: profile to configure the experiment
        :type profile: class Profile

        Experiment start steps

        1) Prepare Gateway
            a) Reset control node
            b) Start control node serial communication
            c) Start measures handler (OML thread)
        2) Prepare Control node
            a) Start Open Node DC (stopped before)
            b) Reset time control node, and update time reference
            c) Configure profile
        3) Prepare Open node
            a) Flash open node
            b) Start open node serial redirection
            c) Start GDB server
        4) Experiment Started

        """

        if self.experiment_is_running:
            LOGGER.warning('Experiment running. Stop previous experiment')
            self.exp_stop()

        self.exp_id = exp_id
        self.user = user
        firmware_path = firmware_path or config.FIRMWARES['idle']
        try:
            _prof = profile or config.default_profile()
            self.profile = Profile(_prof, config.board_type())
        except ValueError:
            LOGGER.error('Invalid profile')
            return 1

        self.experiment_is_running = True

        ret_val = 0
        # start steps described in docstring

        # # # # # # # # # #
        # Prepare Gateway #
        # # # # # # # # # #
        ret = self.node_soft_reset('gwt')
        ret_val += ret
        time.sleep(1)  # wait CN started
        ret = self.cn_serial.start(user=self.user, exp_id=self.exp_id)
        ret_val += ret

        # # # # # # # # # # # # #
        # Prepare Control Node  #
        # # # # # # # # # # # # #
        ret = self.protocol.green_led_blink()
        ret_val += ret
        ret = self.open_power_start(power='dc')
        ret_val += ret
        ret = self.reset_time()
        ret_val += ret
        ret = self.exp_update_profile()
        ret_val += ret

        # # # # # # # # # # #
        # Prepare Open Node #
        # # # # # # # # # # #
        if config.board_type() == 'M3':
            ret = self.node_flash('m3', firmware_path)
            ret_val += ret
            ret = self.serial_redirection.start()
            ret_val += ret
            # ret = self.gdb_server.start()
            # ret_val += ret
        elif config.board_type() == 'A8':
            pass
        else:  # pragma: no cover
            raise NotImplementedError('Board type not managed')

        if config.robot_type() == 'roomba':
            LOGGER.info("I'm a roomba")
            LOGGER.info("Running Start Roomba")

        return ret_val

    def exp_stop(self):
        """
        Stop the current running experiment

        Experiment stop steps

        1) Cleanup Control node config
            a) Stop measures Control Node, Configure profile == None
            b) Start Open Node DC (may be running on battery)
        2) Cleanup open node
            a) Stop GDB server
            b) Stop open node serial redirection
            c) Flash Idle open node (when DC)
            d) Shutdown open node (DC)
        3) Cleanup control node interraction
            a) Stop control node serial communication
        4) Cleanup Manager state
        5) Experiment Stopped

        """
        if not self.experiment_is_running:
            LOGGER.warning("No experiment running. Don't stop")
            return 0
        ret_val = 0

        # # # # # # # # # # # # # # # #
        # Cleanup Control node config #
        # # # # # # # # # # # # # # # #

        self.profile = Profile(config.default_profile(), config.board_type())
        ret = self.exp_update_profile()
        ret_val += ret
        ret = self.open_power_start(power='dc')
        ret_val += ret
        ret = self.protocol.green_led_on()
        ret_val += ret

        if config.robot_type() == 'roomba':
            LOGGER.info("I'm a roomba")
            LOGGER.info("Running stop Roomba")

        # # # # # # # # # # #
        # Cleanup open node #
        # # # # # # # # # # #
        if config.board_type() == 'M3':
            # ret = self.gdb_server.stop()
            # ret_val += ret
            ret = self.serial_redirection.stop()
            ret_val += ret
            ret = self.node_flash('m3', config.FIRMWARES['idle'])
            ret_val += ret
        elif config.board_type() == 'A8':
            pass
        else:  # pragma: no cover
            raise NotImplementedError('Board type not managed')
        ret = self.open_power_stop(power='dc')
        ret_val += ret

        # # # # # # # # # # # # # # # # # # #
        # Cleanup control node interraction #
        # # # # # # # # # # # # # # # # # # #
        self.cn_serial.stop()

        # Reset configuration
        self.user = None
        self.exp_id = None
        self.experiment_is_running = False

        return ret_val

    def exp_update_profile(self, profile=None):
        """
        Update the control node profile
        """
        if profile is not None:
            self.profile = profile
        LOGGER.debug('Update profile')

        ret = 0
        # power_mode (keep open node started/stoped state)
        ret += self.protocol.start_stop(
            self.open_node_state, self.profile.power)
        # Consumption
        ret += self.protocol.config_consumption(self.profile.consumption)
        # Radio
        ret += self.protocol.config_radio(self.profile.radio)

        if ret != 0:  # pragma: no cover
            LOGGER.error('Profile update failed')
        return ret

    def reset_time(self):
        """
        Reset control node time and update absolute time reference

        Updating time reference is propagated to measures handler
        """
        LOGGER.debug('Reset control node time')
        ret = self.protocol.reset_time()
        if ret != 0:  # pragma: no cover
            LOGGER.error('Reset time failed')
        return ret

    def open_power_start(self, power=None):
        """ Power on the open node """
        LOGGER.debug('Open power start')
        if power is None:
            assert self.profile is not None
            power = self.profile.power

        ret = self.protocol.start_stop('start', power)

        if ret != 0:  # pragma: no cover
            LOGGER.error('Open power start failed')
        else:
            self.open_node_state = "start"
        return ret

    def open_power_stop(self, power=None):
        """ Power off the open node """
        LOGGER.debug('Open power stop')
        if power is None:
            assert self.profile is not None
            power = self.profile.power

        ret = self.protocol.start_stop('stop', power)

        if ret != 0:  # pragma: no cover
            LOGGER.error('Open power stop failed')
        else:
            self.open_node_state = "stop"
        return ret

    @staticmethod
    def node_soft_reset(node):
        """
        Reset the given node using reset pin

        :param node: Node name in {'gwt', 'm3'}
        """
        assert node in ['gwt', 'm3'], "Invalid node name"
        LOGGER.debug('Node %s reset', node)

        ret, _ = openocd_cmd.reset(node)

        if ret != 0:  # pragma: no cover
            LOGGER.error('Node %s reset failed: %d', node, ret)

        return ret

    @staticmethod
    def node_flash(node, firmware_path):
        """
        Flash the given firmware on the given node

        :param node: Node name in {'gwt', 'm3'}
        :param firmware_path: Path to the firmware to be flashed on `node`.
        """
        assert node in ['gwt', 'm3'], "Invalid node name"
        LOGGER.debug('Flash firmware on %s: %s', node, firmware_path)

        ret, _ = openocd_cmd.flash(node, firmware_path)

        if ret != 0:  # pragma: no cover
            LOGGER.error('Flash firmware failed on %s: %d', node, ret)
        return ret

    def auto_tests(self, channel, blink, flash, gps):
        """
        Run Auto-tests on nodes and gateway
        """
        autotest_manager = autotest.AutoTestManager(self)
        return autotest_manager.auto_tests(channel, blink, flash, gps)
