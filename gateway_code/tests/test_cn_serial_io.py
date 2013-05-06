#! /usr/bin/env python
# -*- coding:utf-8 -*-

import mock
import unittest

from gateway_code import cn_serial_io
from gateway_code.cn_serial_io import SYNC_BYTE
import serial
import time
import threading

class TestsCnSerialIo(unittest.TestCase):

    def setUp(self):
        self.unlock_test = threading.Event()

        self.serial_patcher = mock.patch('serial.Serial')
        serial_class_mock   = self.serial_patcher.start()
        serial_mock         = serial_class_mock.return_value

        serial_mock.read.side_effect  = self._read_mock
        def mock_close():
            serial_mock.read.side_effect = serial.SerialException
        serial_mock.close.side_effect = mock_close

    def tearDown(self):
        self.serial_patcher.stop()

    def _read_mock(self, val=1):
        result = ''
        try:
            for _i in range(0, val):
                result += self.read_values.pop(0)
        except IndexError: # last Item
            time.sleep(0.1)
            if result == '':
                self.unlock_test.set()
        return result




    def test_rx_wih_invalid_start(self):
        """ Test reception with invalid bytes at start """

        self.read_values = ['D', 'D', 'E','K','K'] + \
                [SYNC_BYTE, chr(3), 'a', 'b', 'c'] + \
                [SYNC_BYTE, chr(1), 'x'] + \
                [SYNC_BYTE, chr(2), SYNC_BYTE, SYNC_BYTE]
        self.result_packets = ['abc', 'x', SYNC_BYTE + SYNC_BYTE]

        def cb_packet_received(pkt):
            result = self.result_packets.pop(0)
            self.assertEquals(pkt, result)

        rxtx = cn_serial_io.RxTxSerial(cb_packet_received)
        rxtx.start()

        # wait until read finished
        self.unlock_test.wait()

        rxtx.stop()


