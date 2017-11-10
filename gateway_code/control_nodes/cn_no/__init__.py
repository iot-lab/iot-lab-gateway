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

"""Control Node experiment implementation no ControlNode."""

import logging

from gateway_code.common import logger_call

LOGGER = logging.getLogger('gateway_code')


class ControlNodeNo(object):
    """ No Control Node """
    TYPE = 'no'
    FEATURES = []

    def __init__(self, node_id, default_profile):
        self.node_id = node_id
        self.default_profile = default_profile
        self.profile = self.default_profile

    @staticmethod
    @logger_call("Control node : Start")
    def start(exp_id, exp_files=None):  # pylint:disable=unused-argument
        """ Start ControlNode serial interface """
        return 0

    @staticmethod
    @logger_call("Control node : Stop")
    def stop():
        """ Start ControlNode """
        return 0

    @staticmethod
    @logger_call("Control node: Setup")
    def setup():
        """Setup control node."""
        return 0

    @staticmethod
    @logger_call("Control node: Flash")
    def flash(*args, **kwargs):
        """Setup control node."""
        return 0

    @logger_call("Control node : Start experiment")
    def start_experiment(self, profile):
        """ Configure the experiment """
        ret_val = 0
        ret_val += self.configure_profile(profile)
        return ret_val

    @logger_call("Control node : Stop the experiment")
    def stop_experiment(self):
        """Cleanup the control node configuration."""
        ret_val = 0
        ret_val += self.configure_profile(None)
        return ret_val

    @staticmethod
    def autotest_setup(measures_handler):
        """Setup for autotests."""
        _ = measures_handler  # pylint:disable=unused-argument
        return 0

    @staticmethod
    def autotest_teardown(stop_on):
        """Teardown autotests."""
        _ = stop_on  # pylint:disable=unused-argument
        return 0

    @logger_call("Control node : profile configuration")
    def configure_profile(self, profile=None):
        """ Configure the given profile on the control node """
        LOGGER.info('Configure profile on Control Node')
        self.profile = profile or self.default_profile
        return 0

    @staticmethod
    def status():
        """ Check Control node status """
        return 0
