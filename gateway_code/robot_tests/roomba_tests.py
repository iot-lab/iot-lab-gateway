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
Test module for Roomba code with the real robot
"""

import time
from gateway_code import gateway_logging
from gateway_code import gateway_roomba


import os
if not os.path.exists(gateway_roomba.TTY):
    import unittest
    raise unittest.SkipTest("Skip roomba tests")


def test1():
    """
    Roomba start, pause, and stop
    """
    gateway_logging.init_logger(".")

    print "Begin Roomba TEST 1"
    robot = gateway_roomba.GatewayRoomba()
    print "Roomba Start, status=", robot.get_status()
    time.sleep(2)
    robot.start()
    time.sleep(10)
    print "Roomba Pause, status=", robot.get_status()
    robot.motion_pause()
    time.sleep(3)
    print "Roomba Continue, status=", robot.get_status()
    robot.motion_continue()
    time.sleep(4)
    print "Roomba Stop, status=", robot.get_status()
    robot.stop()
    time.sleep(28)
    print "Roomba Close, status", robot.get_status()
    robot.close_roomba()
    print "End  Roomba TEST 1"

    return
