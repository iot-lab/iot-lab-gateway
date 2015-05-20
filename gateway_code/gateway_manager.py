#! /usr/bin/env python
# -*- coding:utf-8 -*-

""" Gateway manager """

from threading import RLock, Timer
import os
import time

import gateway_code.config as config
from gateway_code import common
from gateway_code.profile import Profile
from gateway_code.autotest import autotest

import gateway_code.open_node

from gateway_code.control_node import cn_interface, cn_protocol, cn
from gateway_code import gateway_logging

LOGGER = gateway_logging.LOGGER


class GatewayManager(object):  # pylint:disable=too-many-instance-attributes
    """
    Gateway Manager class,

    Manages experiments, open node and control node
    """
    board_type = None
    default_profile = None

    open_nodes = {'m3': gateway_code.open_node.NodeM3,
                  'a8': gateway_code.open_node.NodeA8}

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
        self.profile = None
        self.open_node_state = "stop"
        self.user_log_handler = None

        self.rlock = RLock()
        self.timeout_timer = None

        gateway_logging.init_logger(log_folder)  # logger config

        self.cn_serial = cn_interface.ControlNodeSerial()
        self.protocol = cn_protocol.Protocol(self.cn_serial.send_command)

        self.open_node = GatewayManager.open_nodes[self.board_type]()
        self.control_node = cn.ControlNode()

        self.nodes = {
            'control': self.control_node,
            'open': self.open_node,
        }

    def setup(self):
        """ Run commands that might crash
        Must be run before running other commands """
        # Setup control node
        ret = self.node_flash('control', None)  # Flash default
        if ret != 0:
            raise StandardError("Control node flash failed: {ret:%d}", ret)

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

        if config.robot_type() == 'turtlebot2':  # pragma: no cover
            LOGGER.info("I'm a Turtlebot2")
            self._create_user_exp_folders(user, exp_id)

        self.create_user_exp_files(user=user, exp_id=exp_id)
        self.user_log_handler = gateway_logging.user_logger(
            self.exp_desc['exp_files']['log'])
        LOGGER.addHandler(self.user_log_handler)

        # Print log after creating user logs
        LOGGER.info('Start experiment: %s-%i', user, exp_id)

        # start steps described in docstring
        ret_val = 0

        # # # # # # # # # #
        # Prepare Gateway #
        # # # # # # # # # #
        ret_val += self.node_soft_reset('control')
        time.sleep(1)  # wait CN started
        ret_val += self.cn_serial.start(exp_desc=self.exp_desc)

        # # # # # # # # # # # # #
        # Prepare Control Node  #
        # # # # # # # # # # # # #
        ret_val += self.protocol.green_led_blink()
        ret_val += self.open_power_start(power='dc')
        ret_val += self.set_time()
        ret_val += self.set_node_id()
        ret_val += self.configure_cn_profile()

        # # # # # # # # # # #
        # Prepare Open Node #
        # # # # # # # # # # #
        # If firmware_path is None, it uses default firmware
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
        LOGGER.info("Timeout experiment: %r %r", user, exp_id)
        if self.exp_desc['exp_id'] == exp_id and self.exp_desc['user'] == user:
            LOGGER.info("Still running. Stop exp")
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

        ret_val += self.exp_update_profile(None)
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
            self.profile = self.default_profile
            return
        try:
            self.profile = Profile(board_type=self.board_type, **profile_dict)
        except (ValueError, TypeError, AssertionError) as err:
            LOGGER.error('Invalid profile: %r', err)
            raise ValueError

    def configure_cn_profile(self):
        """ Configure the control node profile """
        LOGGER.info('Configure profile on control node')

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
        """ Set control node time to current time

        Updating time reference is propagated to measures handler
        """
        LOGGER.debug('Set control node time')
        ret = self.protocol.set_time()
        if ret != 0:  # pragma: no cover
            LOGGER.error('Set time failed')
        return ret

    @common.syncronous('rlock')
    def set_node_id(self):
        """ Set the node_id on the control node """
        LOGGER.debug('Set node id')
        ret = self.protocol.set_node_id()

        if ret != 0:  # pragma: no cover
            LOGGER.error('Set node id failed')
        return ret

    @common.syncronous('rlock')
    def open_power_start(self, power=None):
        """ Power on the open node """
        LOGGER.info('Open power start')
        power = power or self.profile.power
        ret = self.protocol.start_stop('start', power)

        if ret != 0:  # pragma: no cover
            LOGGER.error('Open power start failed')
        else:
            self.open_node_state = "start"
        return ret

    @common.syncronous('rlock')
    def open_power_stop(self, power=None):
        """ Power off the open node """
        LOGGER.info('Open power stop')
        power = power or self.profile.power

        ret = self.protocol.start_stop('stop', power)

        if ret != 0:  # pragma: no cover
            LOGGER.error('Open power stop failed')
        else:
            self.open_node_state = "stop"
        return ret

    @common.syncronous('rlock')
    def open_debug_start(self):
        """ Start open node debugger """
        LOGGER.info('Open node debugger start')

        ret = self.nodes['open'].debug_start()
        if ret != 0:  # pragma: no cover
            LOGGER.error('Open node debugger start failed')
        return ret

    @common.syncronous('rlock')
    def open_debug_stop(self):
        """ Stop open node debugger """
        LOGGER.info('Open node debugger stop')

        ret = self.nodes['open'].debug_stop()
        if ret != 0:  # pragma: no cover
            LOGGER.error('Open node debugger stop failed')
        return ret

    @common.syncronous('rlock')
    def node_soft_reset(self, node):
        """
        Reset the given node using reset pin

        :param node: Node type in {'control', 'open'}
        """
        assert node in ['control', 'open'], "Invalid node type"
        LOGGER.info('Node %s reset', node)

        ret = self.nodes[node].reset()

        if ret != 0:  # pragma: no cover
            LOGGER.error('Reset failed on %s node: %d', node, ret)
        return ret

    @common.syncronous('rlock')
    def node_flash(self, node, firmware_path):
        """
        Flash the given firmware on the given node

        :param node: Node name in {'control', 'open'}
        :param firmware_path: Path to the firmware to be flashed on `node`.
        """
        assert node in ['control', 'open'], "Invalid node name"
        LOGGER.info('Flash firmware on %s node: %s', node, firmware_path)

        ret = self.nodes[node].flash(firmware_path)

        if ret != 0:  # pragma: no cover
            LOGGER.error('Flash firmware failed on %s node: %d', node, ret)
        return ret

    @common.syncronous('rlock')
    def auto_tests(self, channel, blink, flash, gps):
        """
        Run Auto-tests on nodes and gateway
        """
        autotest_manager = autotest.AutoTestManager(self)
        return autotest_manager.auto_tests(channel, blink, flash, gps)

    @common.syncronous('rlock')
    def status(self):
        """ Run a node sanity status check """
        ret = 0
        ret += self.control_node.status()
        ret += self.open_node.status()
        return ret

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
