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


""" Module managing the open node RTL SDR TCP server """

import os
import shlex

import logging

from .external_process import ExternalProcess

LOGGER = logging.getLogger('gateway_code')

LOG_DIR = '/var/log/gateway-server'
RTL_TCP_LOG_FILE = os.path.join(LOG_DIR, 'rtl_tcp.log')


class RtlTcp(ExternalProcess):
    """ Class providing node RTL SDR TCP server

    It's implemented as a stoppable thread running rtl_tcp in a loop.
    """
    RTL_TCP = ('/usr/bin/rtl_tcp '
               '-a 0.0.0.0 '
               '-p {port} '
               '-f {frequency}')
    NAME = "rtl_tcp"

    def __init__(self, port, frequency):
        self.process_cmd = shlex.split(self.RTL_TCP.format(
            port=port, frequency=frequency))
        self.stdout = open(RTL_TCP_LOG_FILE, 'w')
        super(RtlTcp, self).__init__()

    def check_error(self, retcode):
        """Print debug message and check error."""
        if retcode and self._run:
            LOGGER.warning('%s error or restarted', self.NAME)
        return retcode
