# -*- coding:utf-8 -*-

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
