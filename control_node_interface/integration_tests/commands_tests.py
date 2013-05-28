#! /usr/bin/env python
# -*- coding:utf-8 -*-

import subprocess

C_PROGRAM = '../control_node_interface'

def test_echo():
    args = [C_PROGRAM]
    COMMANDS = """start dc
    stop batt
    reset_time"""

    RET = """ACK
    ACK
    ACK"""

    program = subprocess.Popen(args, stdin=subprocess.PIPE, \
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = program.communicate(COMMANDS)

    print out, err
    assert out == RET


