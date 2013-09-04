#! /usr/bin/python
# -*- coding:utf-8 -*-


"""
Open node validation interface

Interface for running autotests with open node auto-test firmware
"""


import threading
import struct
import serial
import Queue


from gateway_code import common
from gateway_code import config


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
    'test_gpio_pps': 0x0A,

    # radio
    'radio_pkt': 0x0B,
    'radio_ping_pong': 0xBB,

    # get_time
    'get_time': 0x0D,
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


class OpenNodeSerial(object):
    """
    OpenNodeSerial class implementing the interface with open node auto-test
    """

    def __init__(self):
        self.serial_fd = None
        self.stop_reader = threading.Event()
        self.msg_queue = Queue.Queue(0)

        self.reader_thread = None

    def start(self):
        """ Start serial interface """
        # open serial
        tty = config.NODES_CFG['m3']['tty']
        baudrate = config.NODES_CFG['m3']['baudrate']
        self.serial_fd = serial.Serial(tty, baudrate, timeout=0.5)
        self.serial_fd.flushInput()

        # start reader thread
        self.reader_thread = threading.Thread(target=self._serial_reader)
        self.reader_thread.start()

    def stop(self):
        """ Start serial interface """
        self.stop_reader.set()
        self.reader_thread.join()
        self.serial_fd.close()

    def send_command(self, command_list):
        """ Send command and wait for answer """
        serial_data = []

        # extract command
        command = command_list.pop(0)
        try:
            serial_data.append(chr(COMMAND_DICT[command]))
        except KeyError:
            raise NotImplementedError

        # extract parameters
        if command in ['leds_on', 'leds_off', 'leds_blink']:
            # extract leds <0-7>
            leds = chr(int(command_list.pop(0)))
            serial_data.append(leds)
            # add <freq> for leds_blink
            if command == 'leds_blink':
                # convert freq to list of bytes
                freq_codes = list(struct.pack('H', int(command_list.pop(0))))
                serial_data.extend(freq_codes)
        elif command in ['radio_pkt', 'radio_ping_pong']:
            # add <power> and <channel>
            pow_code = chr(RADIO_POW_DICT[command_list.pop(0)])
            channel = chr(int(command_list.pop(0)))
            serial_data.append(pow_code)
            serial_data.append(channel)
        else:  # command without parameter get_<sensor> or test_<feature>
            pass

        # send command
        ret = self._serial_send_cmd(serial_data)
        return ret

    def _serial_send_cmd(self, chars_list):
        """ Serial level level command send implementation """

        # create packet with header
        packet = ''.join([SYNC_BYTE, chr(len(chars_list))] + chars_list)
        self.serial_fd.write(packet)

        # wait answer
        common.empty_queue(self.msg_queue)
        try:
            answer = self.msg_queue.get(timeout=10).split(' ')
        except Queue.Empty:
            answer = None
        return answer

    def _serial_reader(self):
        """ Serial port reader thread """
        read_str = ''
        while not self.stop_reader.is_set():
            read_str += self.serial_fd.readline()  # append waiting data
            if not read_str or read_str[-1] != '\n':  # timeout reached
                continue
            # answer complete
            self.msg_queue.put(read_str.strip())
            read_str = ''
