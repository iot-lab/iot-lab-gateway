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

"""
    Open Node Openmoteb experiment implementation.

    Openmoteb lifecycle is handled by a Segger J-Link (JTAG).
    In this setup, both Openmoteb and Segger J-Link use an USB port each.
    Openmoteb serial port is accessed via it's own USB port.

    +------------+
    |JLINK Segger|===  USB port (99-jlink.rules)
    +------------+
          |
        JTAG
          |
    +------------+
    | Openmoteb  |===  USB port ttyON_OPENMOTEB (openmoteb.rules)
    +------------+
"""

from gateway_code.config import static_path
from gateway_code.open_nodes.common.node_segger import NodeSeggerBase


class NodeOpenmoteb(NodeSeggerBase):
    """ Open node Openmoteb implementation """

    TYPE = 'openmoteb'
    FW_IDLE = static_path('openmote-b_idle.elf')
    FW_AUTOTEST = static_path('openmote-b_autotest.elf')
    JLINK_DEVICE = "CC2538SF53"
    JLINK_IF = "JTAG"
    JLINK_RESET_FILE = static_path("openmoteb_reset.seg")
    # CC2538 default flash_addr 0x200000
    JLINK_FLASH_ADDR = 0x200000
    TTY = '/dev/iotlab/ttyON_OPENMOTEB'
    BAUDRATE = 115200
