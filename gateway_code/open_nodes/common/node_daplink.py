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

""" Open Node based on DAP Link programmer implementation """

from gateway_code.open_nodes.common.node_openocd import NodeOpenOCDBase


class NodeDapLinkBase(NodeOpenOCDBase):
    # pylint:disable=no-member
    """ Open node DAP Link based board implementation """

    OPENOCD_SERIAL_CMD = "-c 'cmsis_dap_serial {serial}'"
    TTY = '/dev/iotlab/ttyON_CMSIS_DAP'
    BAUDRATE = 115200
