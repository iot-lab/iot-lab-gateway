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

""" Open Node NRF52832-MDK experiment implementation """

from gateway_code.config import static_path
from gateway_code.open_nodes.common.node_openocd import NodeOpenOCDBase


class NodeNrf52832Mdk(NodeOpenOCDBase):
    """ Open node NRF52832-MDK implementation """

    TYPE = 'nrf52832mdk'
    OPENOCD_PATH = '/opt/openocd-dev/bin/openocd'
    OPENOCD_CFG_FILE = static_path('iot-lab-nrf528xxmdk.cfg')
    FW_IDLE = static_path('nrf52832mdk_idle.elf')
    FW_AUTOTEST = static_path('nrf52832mdk_autotest.elf')
    TTY = '/dev/iotlab/ttyON_CMSIS-DAP'
    BAUDRATE = 115200
