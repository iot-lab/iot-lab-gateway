#! /usr/bin/python
# -*- coding:utf-8 -*-


"""
Simple expect implementation

Author: Gaëtan Harter gaetan.harter@inria.fr
"""

import re
import time
import sys
import serial


class SerialExpect(object):
    """ Simple Expect implementation for serial """

    def __init__(self, tty, baudrate):
        self.serial_fd = serial.Serial(tty, baudrate, timeout=0.1)
        self.serial_fd.flushInput()

    def __del__(self):
        self.serial_fd.close()

    def expect_list(self, pattern_list, timeout=-1):
        """ expect multiple patterns """
        # concatenate in a single pattern
        pattern = '(' + ')|('.join(pattern_list) + ')'
        return self.expect(pattern, timeout)

    def expect(self, pattern, timeout=-1):
        """ expect pattern
        return matching string on match
        return '' on timeout
        It cannot match multiline pattern correctly """

        if '\n' in pattern:
            print 'expect cannot accurately match multiline patterns'
            print 'it may fail depending on the runtime cases'

        end_time = None
        if timeout >= 0:
            end_time = time.time() + timeout

        buff = ''
        regexp = re.compile(pattern)
        while True:
            # keep only last line in buffer (no multiline assurance)
            buff = buff.split('\n')[-1]

            # get new data
            read_bytes = self.serial_fd.read(size=16)  # timeout 0.1
            sys.stdout.write(read_bytes)
            sys.stdout.flush()

            buff += read_bytes

            match = regexp.search(buff)
            if match:
                return match.group(0)
            elif end_time is not None and end_time <= time.time():
                return ''  # timeout
            # continue
