#! /usr/bin/python
# -*- coding:utf-8 -*-


"""
Simple expect implementation

Author: Gaëtan Harter gaetan.harter@inria.fr
"""

import re
import time
import serial


class SerialExpect(object):
    """ Simple Expect implementation for serial """

    def __init__(self, tty, baudrate, logger=None):
        self.serial_fd = serial.Serial(tty, baudrate, timeout=0.1)
        self.serial_fd.flushInput()
        self.logger = logger

    def send(self, data):
        """ Write given data to serial with newline"""
        self.serial_fd.write(data + '\n')

    def expect_list(self, pattern_list, timeout=float('+inf')):
        """ expect multiple patterns """
        # concatenate in a single pattern
        pattern = '(' + ')|('.join(pattern_list) + ')'
        return self.expect(pattern, timeout)

    def expect(self, pattern, timeout=float('+inf')):
        """ expect pattern
        return matching string on match
        return '' on timeout
        It cannot match multiline pattern correctly """

        if '\n' in pattern:
            raise ValueError("Does not handle multiline patterns with '\\n'")

        end_time = time.time() + timeout

        buff = ''
        print_buff = ''
        regexp = re.compile(pattern)
        while True:
            # get new data
            try:
                read_bytes = self.serial_fd.read(size=16)  # timeout 0.1
            except serial.SerialException:
                return ''

            if end_time <= time.time():
                # last read_bytes may not be printed but don't care
                return ''  # timeout

            # no data, continue
            if not read_bytes:
                continue

            # add new bytes to remaining of last line
            # no multiline patterns
            buff = buff.split('\n')[-1] + read_bytes

            # print each line with timestamp on front
            if self.logger is not None:
                print_buff += read_bytes
                lines = print_buff.splitlines()

                # keep last line in buffer if not newline terminated
                if print_buff[-1] not in '\r\n':
                    print_buff = lines.pop(-1)
                else:
                    print_buff = ''

                # print all lines
                for line in lines:
                    self.logger.debug(line)

            match = regexp.search(buff)
            if match:
                # print last lines in case
                if self.logger is not None:
                    self.logger.debug(print_buff)
                return match.group(0)

            # continue
