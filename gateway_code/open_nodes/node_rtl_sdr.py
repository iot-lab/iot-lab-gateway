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

""" Open Node Rtl SDR experiment implementation """

import logging
import shlex
import subprocess

import gateway_code.utils.ftdi_check

from gateway_code.common import logger_call
from gateway_code.utils.rtl_tcp import RtlTcp
from gateway_code.open_nodes.common.node_no import NodeNoBase

LOGGER = logging.getLogger('gateway_code')

# This command controls the power of the open node/rtl_tcp USB stick via the
# Yepkit module.
YKUSHCMD = "sudo ykushcmd {model} {cmd} {port}"


class NodeRtlSdr(NodeNoBase):
    """ Open node Rtl SDR implementation """

    TYPE = 'rtl_sdr'
    RTL_TCP_PORT = 50000
    RTL_TCP_FREQ = 868000000

    def __init__(self):
        self.rtl_tcp = RtlTcp(self.RTL_TCP_PORT, self.RTL_TCP_FREQ)

    @logger_call("Node No: Setup of no node")
    def setup(self, firmware_path=None):
        """Power up the SDR dongle and start rtl_tcp server."""
        ykushcmd_str = YKUSHCMD.format(model="", cmd="-u", port="3")
        ret_val = subprocess.call(shlex.split(ykushcmd_str))
        ret_val += self.rtl_tcp.start()
        return ret_val

    @logger_call("Node No: teardown of no node")
    def teardown(self):
        """Stop rtl_tcp server and poweroff the SDR dongle."""
        ret_val = self.rtl_tcp.stop()
        ykushcmd_str = YKUSHCMD.format(model="", cmd="-d", port="3")
        ret_val += subprocess.call(shlex.split(ykushcmd_str))
        return ret_val
