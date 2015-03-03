#! /usr/bin/python
# -*- coding:utf-8 -*-

import sys
import time
from gateway_code.autotest import m3_node_interface


SYNC_BYTE = chr(0x80)

COMMAND_DICT = {

    # leds
    'leds_on': 0x00,
    'leds_off': 0x01,
    'leds_blink': 0x02,

    # sensors
    'get_light': 0x03,
    'get_pressure': 0x04,
    # IMU: inertial measurement unit
    'get_gyro': 0x05,
    'get_accelero': 0x06,
    'get_magneto': 0x07,
    # flash
    'test_flash': 0x08,
    # TBD
    'test_i2c': 0x09,
    'test_pps_start': 0x0A,
    'test_pps_stop': 0x1A,
    'test_pps_get': 0x2A,
    'test_gpio': 0xBE,

    # radio
    'radio_pkt': 0x0B,
    'radio_ping_pong': 0xBB,

    # get_time
    'get_time': 0x0D,
    'get_uid': 0x0E,
}


RADIO_POW_DICT = {
    '3dBm': 38,
    '2.8dBm': 37,
    '2.3dBm': 36,
    '1.8dBm': 34,
    '1.3dBm': 33,
    '0.7dBm': 31,
    '0dBm': 30,
    '-1dBm': 29,
    '-2dBm': 28,
    '-3dBm': 27,
    '-4dBm': 26,
    '-5dBm': 25,
    '-7dBm': 23,
    '-9dBm': 21,
    '-12dBm': 18,
    '-17dBm': 13,
}


class CommandSender(object):

    def __init__(self, input_fd, tty_path):
        self.m3_serial = m3_node_interface.OpenNodeSerial()
        self.tty = tty_path
        self.input_fd = input_fd

    def run(self):
        """ Start m3 serial interface and start sending commands """
        try:
            self.m3_serial.start(self.tty)
            self.read_commands(self.input_fd)
        except Exception as err:
            print >> sys.stderr, str(err)
        finally:
            print >> sys.stderr, "Exiting"
            self.m3_serial.stop()

    def read_commands(self, input_fd):
        """ Read commands from file """
        while True:
            time.sleep(1)  # sleep between  each line
            line = input_fd.readline()
            if line == '':
                break
            command = line.strip()

            # skip blank lines and comments
            if len(command) != 0 and command[0] != '#':
                print '%f: Command: %r' % (time.time(), command)
                answer = self._send_cmd(command)
                print '%f: Answer:  %r' % (time.time(), answer)

    def _send_cmd(self, command):
        """ Send and wait answer from open node """
        command_list = [el for el in command.split(' ') if el != '']
        answer = self.m3_serial.send_command(command_list)

        if answer is not None:
            answer = ' '.join(answer)
        return answer


def main(input_fd, tty_path):
    """
    Delay-cat the file.
    Print all non empty lines and sleep 1 second after each line.

    Empty lines in the file are meant to be used as delay.
    """
    command_sender = CommandSender(input_fd, tty_path)
    command_sender.run()


if __name__ == '__main__':
    print >> sys.stderr, ' '.join(sys.argv)
    if len(sys.argv) != 3:
        print >> sys.stderr, "Usage: %s <tty> <command_file>" % sys.argv[0]
        print >> sys.stderr, "If command_file == - use stdin"
        exit(1)

    TTY = sys.argv[1]
    COMMAND_FILE_PATH = sys.argv[2]

    # check stdin
    if COMMAND_FILE_PATH == '-':
        INPUT_FD = sys.stdin
    else:
        INPUT_FD = open(COMMAND_FILE_PATH)

    main(INPUT_FD, TTY)
    INPUT_FD.close()
