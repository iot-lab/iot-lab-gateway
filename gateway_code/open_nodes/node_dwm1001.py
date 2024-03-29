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

""" Open Node DWM1001 experiment implementation """

from gateway_code.config import static_path
from gateway_code.open_nodes.common.node_jlink import NodeJLinkBase


class NodeDwm1001(NodeJLinkBase):
    """ Open node DWM1001 implementation """

    TYPE = 'dwm1001'
    OPENOCD_CFG_FILE = static_path('iot-lab-nrf52xxxdk.cfg')
    OPENOCD_PATH = '/usr/local/bin/openocd'
    FW_IDLE = static_path('dwm1001_idle.elf')
    FW_AUTOTEST = static_path('dwm1001_autotest.elf')
