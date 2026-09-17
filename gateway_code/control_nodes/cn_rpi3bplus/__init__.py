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

"""Control Node experiment implementation RPI3 ControlNode."""

import os.path
import logging
import shlex

from gateway_code.common import logger_call
from gateway_code.nodes import ControlNodeBase
from gateway_code.utils import subprocess_timeout

from gateway_code import config

LOGGER = logging.getLogger('gateway_code')

LOCAL_CONFIG_DIR = '/var/local/config'

# Start power for all USB devices on hub
# ./uhubctl-bin -l 1-1 -p 2 -a 1
# Stop power for all USB devices on hub
# ./uhubctl-bin -l 1-1 -p 2 -a 3
UHUBCTL_BIN = "sudo /usr/bin/uhubctl -l 1-1 -p 2 -a {}"

# Rpi3bplus udev port number (kernel 5.4.72)
# Needed to properly remove the device after USB power off
# +--------------+------------+
# | port 1-1.1.2 | port 1-1.3 |
# | port 1-1.1.3 | port 1-1.2 |
# +--------------+------------+
ON_USBPORT_CONFIG = os.path.join(LOCAL_CONFIG_DIR, 'on_usbport')
ON_USBPORT_DEFAULT = '1-1.2'
UDEVADM_BIN = "sudo udevadm trigger --action=remove /sys/bus/usb/devices/{}"

def _call_cmd(command_str):
    """ Run the given command_str."""

    kwargs = {'args': shlex.split(command_str)}
    try:
        return subprocess_timeout.call(**kwargs)
    except subprocess_timeout.TimeoutExpired as exc:
        LOGGER.error("Command '%s' timeout: %s", command_str, exc)
        return 1

class ControlNodeRpi3bplus(ControlNodeBase):
    """ No Control Node """
    TYPE = 'rpi3bplus'
    FEATURES = ['open_node_power']

    def __init__(self, node_id, default_profile):
        self.node_id = node_id
        self.default_profile = default_profile
        self.profile = self.default_profile
        self.open_node_state = 'stop'

    @property
    def programmer(self):
        """No programmer is available on this type of control node."""
        return None

    @logger_call("Control node: Start")
    def start(self, exp_id, exp_files=None):  # pylint:disable=unused-argument
        """ Start ControlNode serial interface """
        ret_val = 0
        ret_val += self.open_start('dc')
        return ret_val

    @logger_call("Control node: Stop")
    def stop(self):
        """ Start ControlNode """
        ret_val = 0
        ret_val += self.open_stop('dc')
        return ret_val

    @staticmethod
    @logger_call("Control node: Setup")
    def setup():
        """Setup control node."""
        return 0

    @logger_call("Control node: start power of open node")
    def open_start(self, power=None):  # pylint:disable=unused-argument
        """ Start open node with 'power' source """
        ret_val = 0
        ret_val += _call_cmd(UHUBCTL_BIN.format("1"))
        if ret_val == 0:
            self.open_node_state = 'start'
        return ret_val

    @logger_call("Control node: stop power of open node")
    def open_stop(self, power=None):  # pylint:disable=unused-argument
        """ Stop open node with 'power' source """
        # Default value if no configuration file provided
        on_usbport = ON_USBPORT_DEFAULT
        ret_val = 0
        ret_val += _call_cmd(UHUBCTL_BIN.format("3"))
        if os.path.isfile(ON_USBPORT_CONFIG):
            # read_config function invert '-' and '_'
            on_usbport = config.read_config('on_usbport').replace('_', '-')
            LOGGER.debug("Read USBPORT")
        ret_val += _call_cmd(UDEVADM_BIN.format(on_usbport))
        if ret_val == 0:
            self.open_node_state = 'stop'
        return ret_val

    @logger_call("Control node: Flash")
    def flash(self, firmware_path=None, binary=False, offset=0):
        # pylint:disable=unused-argument
        """Flash control node"""
        return 0

    @logger_call("Control node: Start experiment")
    def start_experiment(self, profile):
        """ Configure the experiment """
        ret_val = 0
        ret_val += self.configure_profile(profile)
        return ret_val

    @logger_call("Control node: Stop the experiment")
    def stop_experiment(self):
        """Cleanup the control node configuration."""
        ret_val = 0
        ret_val += self.configure_profile(None)
        ret_val += self.open_start('dc')
        return ret_val

    def autotest_setup(self, measures_handler):
        """Setup for autotests."""
        return 0

    def autotest_teardown(self, stop_on):
        """Teardown autotests."""
        return 0

    @logger_call("Control node: profile configuration")
    def configure_profile(self, profile=None):
        """ Configure the given profile on the control node """
        LOGGER.info('Configure profile on Control Node')
        self.profile = profile or self.default_profile
        return 0

    def status(self):
        """ Check Control node status """
        return 0
