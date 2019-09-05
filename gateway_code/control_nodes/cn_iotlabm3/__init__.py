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

""" Standalone Control Node experiment implementation """

import logging
import gateway_code.utils.ftdi_check
from gateway_code.common import logger_call
from gateway_code.config import static_path

from gateway_code.control_nodes.cn_iotlab import ControlNodeIotlab

LOGGER = logging.getLogger('gateway_code')


class ControlNodeIotlabm3(ControlNodeIotlab):
    """ Implementation of a Control Node with a Standalone M3 """
    TYPE = 'iotlabm3'
    FEATURES = ['leds',
                'radio']
    OPENOCD_PATH = '/opt/openocd-dev/bin/openocd'
    OPENOCD_CFG_FILE = static_path('iot-lab-cn-m3.cfg')

    @logger_call("Control node : profile configuration")
    def configure_profile(self, profile=None):
        """ Configure the given profile on the control node """
        LOGGER.info('Configure profile on Control Node')
        self.profile = profile or self.default_profile
        ret_val = 0

        # Monitoring : Radio only, ignore other fields
        ret_val += self.protocol.config_radio(self.profile.radio)
        return ret_val

    @logger_call("Control node : start power of open node - Ignored")
    def open_start(self, power=None):
        """ Start open node with 'power' source """
        return 0

    @logger_call("Control node : stop power of open node - Ignored")
    def open_stop(self, power=None):
        """ Stop open node with 'power' source """
        return 0

    @staticmethod
    def status():
        """ Check Control node status """
        return gateway_code.utils.ftdi_check.ftdi_check('controlNode', '2232')
