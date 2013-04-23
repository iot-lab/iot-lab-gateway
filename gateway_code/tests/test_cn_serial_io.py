#! /usr/bin/env python
# -*- coding:utf-8 -*-

import mock

from gateway_code import cn_serial_io
import serial
import time
import threading


@mock.patch('serial.Serial')
def test_rx_wih_invalid_start(serial_mock_class):

    # configure test (invalid values at start)
    read_values = ['D', 'D', 'E','K','K'] + \
            [cn_serial_io.SYNC_BYTE, chr(3), 'a', 'b', 'c'] + \
            [cn_serial_io.SYNC_BYTE, chr(1), 'x'] + \
            [cn_serial_io.SYNC_BYTE, chr(2), cn_serial_io.SYNC_BYTE, cn_serial_io.SYNC_BYTE]
    result_packets = ['abc', 'x', cn_serial_io.SYNC_BYTE + cn_serial_io.SYNC_BYTE]

    unlock_test = threading.Event()

    def read_one_val():
        if read_values == []:
            time.sleep(0.1)
            return ''
        return read_values.pop(0)

    def read_mock(val=1):
        result = ''
        for _i in range(0, val):
            ret = read_one_val()
            result += ret
            if ret == '':
                break
        if result == '':
            unlock_test.set()
        return result

    def cb_packet_received(packet):
        assert packet == result_packets.pop(0)

    serial_mock = serial_mock_class.return_value
    serial_mock.read.side_effect = read_mock

    def serial_exception(val=1):
        raise serial.SerialException
    def mock_close():
        serial_mock.read.side_effect = serial_exception
    serial_mock.close.side_effect = mock_close


    rxtx = cn_serial_io.RxTxSerial(cb_packet_received)
    rxtx.start()

    # wait until read finished
    unlock_test.wait()

    rxtx.stop()


