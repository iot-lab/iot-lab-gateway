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

""" Open Node LoRa gateway experiment implementation """

import os
import time
import logging
import shlex
import subprocess

from gateway_code.common import logger_call
from gateway_code.open_nodes.common.node_no import NodeNoBase
from gateway_code.utils.lora_gateway_bridge import LoraGatewayBridge
from gateway_code.utils.mosquitto import Mosquitto

LOGGER = logging.getLogger('gateway_code')
LOG_DIR = '/var/log/gateway-server'
LORA_PKT_FORWARDER_START_CMD = ('sudo '  # needs to be root to access GPIO
                                'CFG_DIR=/var/local/config /opt/lora/start.sh')
LORA_PKT_FORWARDER_MAX_TRIES = 50


class NodeLoraGateway(NodeNoBase):
    """ Open node LoRa gateway implementation """

    TYPE = 'lora_gw'
    MOSQUITTO_PORT = 1883

    def __init__(self):
        self.lora_pkt_fwd_out = open(os.devnull, 'w')
        self._start_lora_pkt_fwd()
        self.mosquitto = Mosquitto(self.MOSQUITTO_PORT)
        self.lora_gateway_bridge = LoraGatewayBridge()

    @staticmethod
    def _lora_pkt_fwd_pid():
        try:
            return subprocess.check_output(shlex.split('pgrep lora_pkt_fwd'))
        except subprocess.CalledProcessError:
            return None

    def _start_lora_pkt_fwd(self):
        _pid = self._lora_pkt_fwd_pid()
        if _pid is None:
            LOGGER.debug("Starting lora_pkt_fwd")
        _tries = 0
        # Sometimes the lora_pkt_forwarder fails to start so try multiple
        # times.
        while _pid is None and _tries <= LORA_PKT_FORWARDER_MAX_TRIES:
            subprocess.Popen(shlex.split(LORA_PKT_FORWARDER_START_CMD),
                             stdout=self.lora_pkt_fwd_out,
                             stderr=self.lora_pkt_fwd_out)
            time.sleep(2)
            _pid = self._lora_pkt_fwd_pid()
            if _pid is None:
                LOGGER.debug("Restarting lora_pkt_fwd")
                _tries += 1
        LOGGER.debug("lora_pkt_forwarder started")

    def __del__(self):
        self.lora_pkt_fwd_out.close()

    @logger_call("Node LoRa gateway: Setup node")
    def setup(self, firmware_path=None):
        """Start mosquitto and the gateway bridge."""
        ret_val = self.mosquitto.start()
        ret_val += self.lora_gateway_bridge.start()
        return ret_val

    @logger_call("Node LoRa gateway: teardown node")
    def teardown(self):
        """Stop the gateway bridge and mosquitto."""
        ret_val = self.lora_gateway_bridge.stop()
        ret_val += self.mosquitto.stop()
        return ret_val
