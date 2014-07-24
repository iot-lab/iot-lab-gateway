#! /usr/bin/env python
# -*- coding:utf-8 -*-


""" Gateway manager """

from threading import RLock, Timer
import os
import time

import gateway_code.config as config
from gateway_code import common
from gateway_code import openocd_cmd
from gateway_code.profile import Profile
from gateway_code.autotest import autotest

import gateway_code.open_node

from gateway_code import control_node_interface, protocol_cn
from gateway_code import gateway_logging

LOGGER = gateway_logging.LOGGER


# Disable: I0011 - 'locally disabling warning'
# too many instance attributes
# pylint:disable=I0011,R0902
class GatewayManager(object):
    """
    Gateway Manager class,

    Manages experiments, open node and control node
    """
    board_type = None
    default_profile = None

    open_nodes = {'M3': gateway_code.open_node.NodeM3,
                  'A8': gateway_code.open_node.NodeA8}

    def __init__(self, log_folder='.'):

        _board_type = config.board_type()
        if _board_type not in GatewayManager.open_nodes:
            raise ValueError('Board type not managed %r' % _board_type)

        # Init class arguments when creating gateway_manager
        # Allows mocking config.board_type in tests
        GatewayManager.board_type = _board_type
        GatewayManager.default_profile = Profile(board_type=_board_type,
                                                 **config.default_profile())

        # current experiment infos
        self.exp_desc = {
            'exp_id': None,
            'user': None,
            'exp_files': {}
        }
        self.experiment_is_running = False
        self.profile = self.default_profile
        self.open_node_state = "stop"
        self.user_log_handler = None

        self.rlock = RLock()
        self.timeout_timer = None

        gateway_logging.init_logger(log_folder)  # logger config

        self.cn_serial = control_node_interface.ControlNodeSerial()
        self.protocol = protocol_cn.Protocol(self.cn_serial.send_command)

        self.open_node = GatewayManager.open_nodes[self.board_type](self)

    def setup(self):
        """ Run commands that might crash
        Must be run before running other commands """
        # Setup control node
        ret = self.node_flash('gwt', config.FIRMWARES['control_node'])
        if ret != 0:
            raise StandardError("Control node flash failed: {ret:%d, '%s')",
                                ret, config.FIRMWARES['control_node'])

    # R0913 too many arguments 6/5
    @common.syncronous('rlock')
    def exp_start(self, user, exp_id,  # pylint: disable=R0913
                  firmware_path=None, profile=None, timeout=0):
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
            LOGGER.debug('Experiment running. Stop previous experiment')
            self.exp_stop()

        try:
            self.decode_and_store_profile(profile)
        except ValueError:
            return 1

        self.experiment_is_running = True

        self.exp_desc['exp_id'] = exp_id
        self.exp_desc['user'] = user

        if config.robot_type() == 'turtlebot':  # pragma: no cover
            LOGGER.info("I'm a Turtlebot")
            self._create_user_exp_folders(user, exp_id)

        self.create_user_exp_files(user=user, exp_id=exp_id)
        self.user_log_handler = gateway_logging.user_logger(
            self.exp_desc['exp_files']['log'])
        LOGGER.addHandler(self.user_log_handler)

        # Print log after creating user logs
        LOGGER.info('Start experiment: %s-%i', user, exp_id)

        firmware_path = firmware_path or config.FIRMWARES['idle']

        # start steps described in docstring
        ret_val = 0

        # # # # # # # # # #
        # Prepare Gateway #
        # # # # # # # # # #
        ret_val += self.node_soft_reset('gwt')
        time.sleep(1)  # wait CN started
        ret_val += self.cn_serial.start(exp_desc=self.exp_desc)

        # # # # # # # # # # # # #
        # Prepare Control Node  #
        # # # # # # # # # # # # #
        ret_val += self.protocol.green_led_blink()
        ret_val += self.open_power_start(power='dc')
        ret_val += self.set_time()
        ret_val += self.configure_cn_profile()

        # # # # # # # # # # #
        # Prepare Open Node #
        # # # # # # # # # # #
        ret_val += self.open_node.setup(firmware_path)

        if timeout != 0:
            LOGGER.debug("Setting timeout to: %d", timeout)
            self.timeout_timer = Timer(timeout, self._timeout_exp_stop,
                                       args=(exp_id, user))
            self.timeout_timer.start()
        LOGGER.info("Start experiment succeeded")
        return ret_val

    @common.syncronous('rlock')
    def _timeout_exp_stop(self, exp_id, user):
        """ Run exp_stop after timeout.

        Should stop only if experiment is the same as the experiment
        that started the timer """
        LOGGER.debug("Timeout experiment: %r %r", user, exp_id)
        if self.exp_desc['exp_id'] == exp_id and self.exp_desc['user'] == user:
            LOGGER.debug("Still running. Stop exp")
            self.exp_stop()

    @common.syncronous('rlock')
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
        LOGGER.info("Stop experiment")

        if not self.experiment_is_running:
            LOGGER.warning("No experiment running. Don't stop")
            return 0
        ret_val = 0
        if self.timeout_timer is not None:
            self.timeout_timer.cancel()
            self.timeout_timer = None

        # # # # # # # # # # # # # # # #
        # Cleanup Control node config #
        # # # # # # # # # # # # # # # #

        self.profile = self.default_profile
        ret_val += self.configure_cn_profile()
        ret_val += self.open_power_start(power='dc')
        ret_val += self.protocol.green_led_on()

        if config.robot_type() == 'roomba':  # pragma: no cover
            LOGGER.info("I'm a roomba")
            LOGGER.info("Running stop Roomba")

        # # # # # # # # # # #
        # Cleanup open node #
        # # # # # # # # # # #
        ret_val += self.open_node.teardown()
        ret_val += self.open_power_stop(power='dc')

        # # # # # # # # # # # # # # # # # # #
        # Cleanup control node interraction #
        # # # # # # # # # # # # # # # # # # #
        self.cn_serial.stop()

        # Remove empty user experiment files
        self.cleanup_user_exp_files()

        # Reset configuration
        self.exp_desc['exp_id'] = None
        self.exp_desc['user'] = None
        self.experiment_is_running = False

        LOGGER.info("Stop experiment succeeded")
        LOGGER.removeHandler(self.user_log_handler)

        return ret_val

    @common.syncronous('rlock')
    def exp_update_profile(self, profile):
        """ Update the experiment profile """
        LOGGER.info('Update experiment profile')

        try:
            self.decode_and_store_profile(profile)
            ret = self.configure_cn_profile()
        except ValueError:
            ret = 1

        if ret != 0:  # pragma: no cover
            LOGGER.error('Update experiment profile failed')
        return ret

    def decode_and_store_profile(self, profile_dict):
        """ Create Profile object from `profile_dict`
        Store Profile in 'self.profile' on success
        :raises: ValueError on invalid profile_dict """
        if profile_dict is None:
            return
        try:
            self.profile = Profile(board_type=self.board_type, **profile_dict)
        except (ValueError, TypeError) as err:
            LOGGER.error('Invalid profile: %r', err)
            raise ValueError

    def configure_cn_profile(self):
        """ Configure the control node profile """
        LOGGER.debug('Configure profile on control node')

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

    @common.syncronous('rlock')
    def set_time(self):
        """
        Reset control node time and update absolute time reference

        Updating time reference is propagated to measures handler
        """
        LOGGER.debug('Reset control node time')
        ret = self.protocol.set_time()
        if ret != 0:  # pragma: no cover
            LOGGER.error('Reset time failed')
        return ret

    @common.syncronous('rlock')
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

    @common.syncronous('rlock')
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

    @common.syncronous('rlock')       # uses `self`
    def node_soft_reset(self, node):  # pylint: disable=R0201

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

    @common.syncronous('rlock')                 # uses `self`
    def node_flash(self, node, firmware_path):  # pylint: disable=R0201
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

    @common.syncronous('rlock')
    def auto_tests(self, channel, blink, flash, gps):
        """
        Run Auto-tests on nodes and gateway
        """
        autotest_manager = autotest.AutoTestManager(self)
        return autotest_manager.auto_tests(channel, blink, flash, gps)

#
# Experiment files and folder management methods
#

    def create_user_exp_files(self, user, exp_id):
        """ Create user experiment files with 0666 permissions """

        exp_files_dir = config.EXP_FILES_DIR.format(user=user, exp_id=exp_id)
        node_id = config.hostname()

        for key, exp_file in config.EXP_FILES.iteritems():
            # calculate file_path and store it in exp_description
            file_path = exp_files_dir + exp_file.format(node_id=node_id)
            self.exp_desc['exp_files'][key] = file_path
            try:
                # create empty file with 0666 permission
                open(file_path, "w").close()
                os.chmod(file_path, config.STAT_0666)
            except IOError as err:
                LOGGER.error('Cannot write exp file: %r', file_path)
                raise err

    def cleanup_user_exp_files(self):
        """ Delete empty user experiment files """
        for exp_file in self.exp_desc['exp_files'].itervalues():
            try:
                if os.path.getsize(exp_file) == 0:
                    os.unlink(exp_file)
            except OSError:
                pass
        self.exp_desc['exp_files'] = {}

# Exp folders creation used in tests

    @staticmethod
    def _create_user_exp_folders(user, exp_id):
        """ Create a user experiment folders

        On turtelbots nodes, the folders can't be created by exp handler
        Also useful for integration tests
        """
        exp_files_dir = config.EXP_FILES_DIR.format(user=user, exp_id=exp_id)
        for file_dir in config.EXP_FILES.iterkeys():
            try:
                os.makedirs(exp_files_dir + file_dir)
            except OSError:
                pass

    @staticmethod
    def _destroy_user_exp_folders(user, exp_id):
        """ Destroy a user experiment folder

        Used in integration tests.
        Implemented here after the '_create' method for completeness """
        exp_files_dir = config.EXP_FILES_DIR.format(user=user, exp_id=exp_id)
        import shutil
        try:
            shutil.rmtree(exp_files_dir)
        except OSError:
            pass
