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
from gateway_code.utils.rtl_tcp import RtlTcp
from gateway_code.utils.mjpg_streamer import MjpgStreamer

LOGGER = logging.getLogger('gateway_code')

LOCAL_CONFIG_DIR = '/var/local/config'
RTL_TCP_CONFIG = os.path.join(LOCAL_CONFIG_DIR, 'rtl_sdr')
CAMERA_CONFIG = os.path.join(LOCAL_CONFIG_DIR, 'camera')

# This command controls the power of the open node/rtl_tcp USB stick via the
# Yepkit module.
YKUSHCMD = "sudo ykushcmd {model} {cmd} {port}"


def _call_cmd(command_str):
    """ Run the given command_str."""

    kwargs = {'args': shlex.split(command_str)}
    try:
        return subprocess_timeout.call(**kwargs)
    except subprocess_timeout.TimeoutExpired as exc:
        LOGGER.error("Command '%s' timeout: %s", command_str, exc)
        return 1


class ControlNodeRpi3(ControlNodeBase):
    """ No Control Node """
    TYPE = 'rpi3'
    FEATURES = ['open_node_power']
    RTL_TCP_PORT = 50000
    RTL_TCP_FREQ = 868000000
    MJPG_STREAMER_PORT = 40000

    def __init__(self, node_id, default_profile):
        self.node_id = node_id
        self.default_profile = default_profile
        self.profile = self.default_profile
        self.open_node_state = 'stop'
        self.rtl_tcp = RtlTcp(self.RTL_TCP_PORT, self.RTL_TCP_FREQ)
        self.mjpg_streamer = MjpgStreamer(self.MJPG_STREAMER_PORT)

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

    @staticmethod
    def _ykush_params(cmd):
        params = {'model': 'ykushxs', 'cmd': cmd, 'port': ''}
        if os.path.isfile(RTL_TCP_CONFIG):
            params['model'] = ''
            params['port'] = '1'
        return params

    @logger_call("Control node: start power of open node")
    def open_start(self, power=None):  # pylint:disable=unused-argument
        """ Start open node with 'power' source """
        ykush_params = self._ykush_params('-u')
        ret_val = 0
        ret_val += _call_cmd(YKUSHCMD.format(**ykush_params))
        if ret_val == 0:
            self.open_node_state = 'start'
        return ret_val

    @logger_call("Control node: stop power of open node")
    def open_stop(self, power=None):  # pylint:disable=unused-argument
        """ Stop open node with 'power' source """
        ykush_params = self._ykush_params('-d')
        ret_val = 0
        ret_val += _call_cmd(YKUSHCMD.format(**ykush_params))
        if ret_val == 0:
            self.open_node_state = 'stop'
        return ret_val

    @logger_call("Control node: Flash")
    def flash(self, firmware_path=None):  # pylint:disable=unused-argument
        """Flash control node"""
        return 0

    @logger_call("Control node: Start experiment")
    def start_experiment(self, profile):
        """ Configure the experiment """
        ret_val = 0
        ret_val += self.configure_profile(profile)
        if os.path.isfile(CAMERA_CONFIG):
            ret_val += self.mjpg_streamer.start()
            LOGGER.debug("Process started: mjpg_streamer, ret: %d", ret_val)
        if os.path.isfile(RTL_TCP_CONFIG):
            ret_val += _call_cmd(YKUSHCMD.format(model="",
                                                 cmd="-u", port="3"))
            ret_val += self.rtl_tcp.start()
            LOGGER.debug("Process started: rtl_tcp, ret: %d", ret_val)
        return ret_val

    @logger_call("Control node: Stop the experiment")
    def stop_experiment(self):
        """Cleanup the control node configuration."""
        ret_val = 0
        ret_val += self.configure_profile(None)
        ret_val += self.open_start('dc')
        if os.path.isfile(CAMERA_CONFIG):
            ret_val += self.mjpg_streamer.stop()
            LOGGER.debug("Process stopped: mjpg_streamer, ret: %d", ret_val)
        if os.path.isfile(RTL_TCP_CONFIG):
            ret_val += _call_cmd(YKUSHCMD.format(model="",
                                                 cmd="-d", port="3"))
            ret_val += self.rtl_tcp.stop()
            LOGGER.debug("Process stopped: rtl_tcp, ret: %d", ret_val)
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
