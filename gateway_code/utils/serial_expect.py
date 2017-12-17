#! /usr/bin/python
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
Simple expect implementation

Author: Gaëtan Harter gaetan.harter@inria.fr
"""

import re
import time
import serial


class SerialExpect(object):
    """ Simple Expect implementation for serial """

    def __init__(self, tty, baudrate, logger=None):
        self.fd = serial.Serial(tty, baudrate,  # pylint:disable=invalid-name
                                timeout=0.1)
        self.logger = logger

    def close(self):
        """ Close connection """
        try:
            self.fd.close()
        except AttributeError:
            pass

    def send(self, data):
        """ Write given data to serial with newline"""
        self.fd.write(data + '\n')

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
                read_bytes = self.fd.read(size=16)  # timeout 0.1
            except (serial.SerialException, AttributeError):
                break

            if end_time <= time.time():
                # last read_bytes may not be printed but don't care
                break  # timeout

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
                    line = line.strip()
                    if line:
                        self.logger.debug(line)

            match = regexp.search(buff)
            if match:
                # print last lines in case
                if self.logger is not None:
                    self.logger.debug(print_buff)
                return match.group(0)

            # continue
        return ''

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        self.close()


class SerialExpectForSocket(SerialExpect):
    """ Simple Expect implementation for tcp connection adapter """

    # Just a hack to use the same class without changing init
    def __init__(self,  # pylint:disable=super-init-not-called
                 host='localhost', port=20000, logger=None):
        url = 'socket://{host}:{port}'.format(host=host, port=port)
        self.fd = self.try_connect(url, timeout=0.1)
        self.logger = logger

    @staticmethod
    def try_connect(url, tries=10, step=0.5, *args, **kwargs):
        """ Try connecting 'tries' time to url tuple
        Sleep 'step' between each tries.
        If last trial fails, the SerialException is raised

        The goal is to be resilient to the fact that serial_aggregator might be
        (re)starting.  """
        # pylint:disable=keyword-arg-before-vararg
        # Run 'tries -1' times with 'try except'
        for _ in range(0, tries - 1):
            try:
                return serial.serial_for_url(url, *args, **kwargs)
            except serial.SerialException:
                time.sleep(step)

        # Last connection should run an exception
        return serial.serial_for_url(url, *args, **kwargs)

    def close(self):
        """ Close connection and wait until it's restartable """
        super(SerialExpectForSocket, self).close()
        time.sleep(1)  # Wait SerialRedirection restarts and can be reconnected
