#! /usr/bin/env python
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


""" Gateway manager """

import os
import time
import errno
from threading import RLock, Timer

import gateway_code.config as config
from gateway_code import common
from gateway_code.common import logger_call
from gateway_code.autotest import autotest
from gateway_code.utils import elftarget

import gateway_code.board_config as board_config

from gateway_code import gateway_logging

LOGGER = gateway_logging.LOGGER


class GatewayManager(object):  # pylint:disable=too-many-instance-attributes
    """ Gateway Manager class,

    Manages experiments, open node and control node """

    def __init__(self, log_folder='.', log_stdout=False):
        gateway_logging.init_logger(log_folder, log_stdout)

        self.board_cfg = board_config.BoardConfig()
        self.rlock = RLock()

        # Nodes instance
        self.open_node = self.board_cfg.board_class()
        self.control_node = self.board_cfg.cn_class(
            self.board_cfg.node_id, self.board_cfg.default_profile)
        self._nodes = {'control': self.control_node, 'open': self.open_node}

        # current experiment infos
        self.exp_id = None
        self.user = None
        self.exp_files = {}

        self.experiment_is_running = False
        self.user_log_handler = None
        self.timeout_timer = None

    @logger_call("Gateway Manager : Setup")
    def setup(self):
        """ Run commands that might crash
        Must be run before running other commands """
        # Setup control node
        ret = self.node_flash('control', None)  # Flash default
        if ret != 0:
            raise StandardError("Control node flash failed: {ret:%d}", ret)

    # R0913 too many arguments 6/5
    @common.syncronous('rlock')
    @logger_call("Gateway Manager : Start experiment")
    def exp_start(self, user, exp_id,  # pylint: disable=R0913
                  firmware_path=None, profile_dict=None, timeout=0):
        """
        Start an experiment

        :param exp_id: experiment id
        :param user: user running the experiment
        :param firmware_path: path of the firmware file to use, can be None
        :param profile_dict: monitoring profile
        :param timeout: Experiment expiration timeout. On 0 no timeout.

        Experiment start steps

        1) Prepare Gateway: User experiment files and log:
        2) Prepare Control node: Start communication and power on open node
        3) Prepare Open node: Check OK, setup firmware and serial redirection
        4) Configure Control Node Profile and experiment
        5) Set Experiment expiration timer

        """
        if self.experiment_is_running:
            LOGGER.debug('Experiment running. Stop previous experiment')
            self.exp_stop()

        try:
            profile = self.board_cfg.profile_from_dict(profile_dict)
        except ValueError as err:
            LOGGER.error('%r', err)
            return 1
        if not elftarget.is_compatible_with_node(firmware_path,
                                                 self.open_node):
            LOGGER.error('Invalid firmware target, aborting experiment.')
            return 1

        ret_val = 0

        self.experiment_is_running = True
        self.exp_id = exp_id
        self.user = user

        if (self.board_cfg.robot_type == 'turtlebot2' or
                self.board_cfg.cn_class.TYPE == 'no'):  # pragma: no cover
            LOGGER.info('Create user exp folder')
            self._create_user_exp_folders(user, exp_id)

        self.exp_files = self.create_user_exp_files(self.board_cfg.node_id,
                                                    user, exp_id)

        # Create user log
        self.user_log_handler = gateway_logging.user_logger(
            self.exp_files['log'])
        LOGGER.addHandler(self.user_log_handler)
        LOGGER.info('Start experiment: %s-%i', user, exp_id)

        # Init ControlNode
        ret_val += self.control_node.start(self.exp_id, self.exp_files)
        # Configure Open Node
        ret_val += self.open_node.setup(firmware_path)
        # Configure experiment and monitoring on ControlNode
        ret_val += self.control_node.start_experiment(profile)

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
        if (self.exp_id, self.user) != (exp_id, user):
            return

        LOGGER.info('Still running. Stop exp')
        try:
            self.exp_stop()
        except EnvironmentError as err:
            if err.errno == errno.EWOULDBLOCK:
                LOGGER.warning('timeout_exp_stop would block hope its OK')
                return
            raise

    @common.syncronous('rlock')
    @logger_call("Gateway Manager : Stop experiment")
    def exp_stop(self):
        """
        Stop the current running experiment

        Experiment stop steps

        1) Clear expiration timeout
        2) Stop OpenNode experiment and reset profile
        3) Cleanup OpenNode
        4) Stop control node
        5) Cleanup empty user experiment files
        """
        LOGGER.info("Stop experiment")

        if not self.experiment_is_running:
            LOGGER.warning("No experiment running. Don't stop")
            return 0
        ret_val = 0
        if self.timeout_timer is not None:
            self.timeout_timer.cancel()
            self.timeout_timer = None

        # Cleanup Control node Monitoring and experiment #
        ret_val += self.control_node.stop_experiment()
        # Cleanup open node
        ret_val += self.open_node.teardown()
        # Stop control node interaction
        self.control_node.stop()

        # Remove empty user experiment files
        self.cleanup_user_exp_files(self.exp_files)
        self.exp_files = {}

        # Reset configuration
        self.exp_id = None
        self.user = None
        self.experiment_is_running = False

        LOGGER.info("Stop experiment succeeded")
        LOGGER.removeHandler(self.user_log_handler)
        self.user_log_handler = None

        return ret_val

    @common.syncronous('rlock')
    def exp_update_profile(self, profile_dict):
        """ Update the experiment profile """
        LOGGER.info('Update experiment profile')

        try:
            profile = self.board_cfg.profile_from_dict(profile_dict)
        except ValueError as err:
            LOGGER.error('%r', err)
            ret = 1
        else:
            ret = self.control_node.configure_profile(profile)

        if ret != 0:  # pragma: no cover
            LOGGER.error('Update experiment profile failed')
        return ret

    @common.syncronous('rlock')
    @logger_call("Gateway Manager : Start open node power")
    def open_power_start(self, power=None):
        """ Power on the open node """
        LOGGER.info('Open power start')
        ret = self.control_node.open_start(power)
        if ret != 0:  # pragma: no cover
            LOGGER.error('Open power start failed')
        return ret

    @common.syncronous('rlock')
    @logger_call("Gateway Manager : Stop open node power")
    def open_power_stop(self, power=None):
        """ Power off the open node """
        LOGGER.info('Open power stop')
        ret = self.control_node.open_stop(power)
        if ret != 0:  # pragma: no cover
            LOGGER.error('Open power stop failed')
        return ret

    @common.syncronous('rlock')
    def open_debug_start(self):
        """ Start open node debugger """
        LOGGER.info('Open node debugger start')

        ret = self._nodes['open'].debug_start()
        if ret != 0:  # pragma: no cover
            LOGGER.error('Open node debugger start failed')
        return ret

    @common.syncronous('rlock')
    def open_debug_stop(self):
        """ Stop open node debugger """
        LOGGER.info('Open node debugger stop')

        ret = self._nodes['open'].debug_stop()
        if ret != 0:  # pragma: no cover
            LOGGER.error('Open node debugger stop failed')
        return ret

    @common.syncronous('rlock')
    @logger_call("Gateway Manager : Soft reset of open node")
    def node_soft_reset(self, node):
        """
        Reset the given node using reset pin

        :param node: Node type in {'control', 'open'}
        """
        assert node in ['control', 'open'], "Invalid node type"
        LOGGER.info('Node %s reset', node)

        ret = self._nodes[node].reset()

        if ret != 0:  # pragma: no cover
            LOGGER.error('Reset failed on %s node: %d', node, ret)
        return ret

    @common.syncronous('rlock')
    @logger_call("Gateway Manager : Flash of node")
    def node_flash(self, node, firmware_path):
        """
        Flash the given firmware on the given node

        :param node: Node name in {'control', 'open'}
        :param firmware_path: Path to the firmware to be flashed on `node`.
        """
        assert node in ['control', 'open'], "Invalid node name"
        LOGGER.info('Flash firmware on %s node: %s', node, firmware_path)

        target_node = self._nodes[node]

        if not elftarget.is_compatible_with_node(firmware_path, target_node):
            LOGGER.error('Invalid firmware target, not flashing.')
            return 1

        ret = target_node.flash(firmware_path)
        if ret != 0:  # pragma: no cover
            LOGGER.error('Flash firmware failed on %s node: %d', node, ret)
        return ret

    @common.syncronous('rlock')
    def auto_tests(self, channel, blink, flash, gps):
        """ Run Auto-tests on nodes and gateway """
        autotest_manager = autotest.AutoTestManager(self)
        return autotest_manager.auto_tests(channel, blink, flash, gps)

    @common.syncronous('rlock')
    def status(self):
        """ Run a node sanity status check """
        ret = 0
        ret += self.control_node.status()
        ret += self.open_node.status()
        return ret

    @common.syncronous('rlock')
    def sleep(self, seconds):  # pylint:disable=no-self-use
        """Sleep `seconds` seconds."""
        time.sleep(seconds)
        return 0

# Experiment files and folder management methods

    @staticmethod
    def create_user_exp_files(node_id, user, exp_id):
        """ Create user experiment files with 0666 permissions """

        exp_dir = config.EXP_FILES_DIR.format(user=user, exp_id=exp_id)
        exp_files = {}

        for name, exp_file in config.EXP_FILES.iteritems():
            file_path = os.path.join(exp_dir, exp_file.format(node_id=node_id))
            exp_files[name] = config.create_user_file(file_path)

        return exp_files

    @staticmethod
    def cleanup_user_exp_files(exp_files):
        """ Delete empty user experiment files """
        for exp_file in exp_files.itervalues():
            config.clean_user_file(exp_file)

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
