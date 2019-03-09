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


"""Module managing the lora gateway bridge tool."""

import os
import shlex

import logging

from .external_process import ExternalProcess

LOGGER = logging.getLogger('gateway_code')
LOG_DIR = '/var/log/gateway-server'
CFG_DIR = '/var/local/config'
LORA_GATEWAY_BRIDGE_DIR = '/opt/lora-gateway-bridge'
LORA_GATEWAY_BRIDGE = os.path.join(LORA_GATEWAY_BRIDGE_DIR,
                                   'lora-gateway-bridge')
LORA_GATEWAY_BRIDGE_CMD = '{bridge} -c {cfg_file}'


class LoraGatewayBridge(ExternalProcess):
    """Class providing node Lora gateway bridge tool

    It's implemented as a stoppable thread running the pkt_forwarder in a loop.
    """
    NAME = "lora_gateway_bridge"

    def __init__(self):
        _bridge_conf_filename = 'lora-gateway-bridge.toml'
        _bridge_cfg = os.path.join(LORA_GATEWAY_BRIDGE_DIR,
                                   _bridge_conf_filename)
        if os.path.isfile(os.path.join(CFG_DIR, _bridge_conf_filename)):
            _bridge_cfg = os.path.join(CFG_DIR, _bridge_conf_filename)
        self.process_cmd = shlex.split(LORA_GATEWAY_BRIDGE_CMD.format(
            bridge=LORA_GATEWAY_BRIDGE, cfg_file=_bridge_cfg))
        super(LoraGatewayBridge, self).__init__()

    def check_error(self, retcode):
        """Print debug message and check error."""
        if retcode and self._run:
            LOGGER.warning('%s error or restarted', self.NAME)
        return retcode
