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

""" Open Node A8-M3 experiment implementation """

import gateway_code.utils.ftdi_check

from gateway_code.config import static_path
from gateway_code.open_nodes.common.node_openocd import NodeOpenOCDBase


class NodeA8M3(NodeOpenOCDBase):
    """ Open node A8-M3 implemenation """

    TYPE = 'a8_m3'
    TTY = '/dev/ttyA8_M3'
    BAUDRATE = 500000
    OPENOCD_PATH = '/opt/openocd-dev/bin/openocd'
    OPENOCD_CFG_FILE = static_path('iot-lab.cfg')
    OPENOCD_OPTS = (static_path('iot-lab-a8-m3.cfg'),)
    FW_IDLE = static_path('a8-m3_idle.elf')
    FW_AUTOTEST = static_path('a8-m3_autotest.elf')
    ALIM = '3.3V'
    AUTOTEST_AVAILABLE = [
        'echo', 'get_time',  # mandatory
        'get_uid',
        'get_accelero', 'get_gyro', 'get_magneto',
        'test_gpio', 'test_i2c',
        'radio_pkt', 'radio_ping_pong',
        'test_pps_start', 'test_pps_get', 'test_pps_stop',
        'leds_on', 'leds_off', 'leds_blink',
    ]

    @staticmethod
    def status():
        """ Check A8-M3 node status """
        return gateway_code.utils.ftdi_check.ftdi_check('a8-m3', '2232')
