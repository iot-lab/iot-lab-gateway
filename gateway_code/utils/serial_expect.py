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
        self.fd = serial.serial_for_url(url, timeout=0.1)
        self.logger = logger

    def close(self):
        """ Close connection and wait until it's restartable """
        super(SerialExpectForSocket, self).close()
        time.sleep(1)  # Wait SerialRedirection restarts and can be reconnected
