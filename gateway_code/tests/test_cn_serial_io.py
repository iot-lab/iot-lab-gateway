#! /usr/bin/env python
# -*- coding:utf-8 -*-

import mock
import select


from gateway_code import cn_serial_io
import Queue
import serial
import sys
import threading


@mock.patch('serial.Serial')
def test_rx_multiple_packets(serial_mock_class):

    rx_queue = Queue.Queue(0)

    # configure test
    read_values = [cn_serial_io.SYNC_BYTE, chr(3), 'a', 'b', 'c'] + \
            [cn_serial_io.SYNC_BYTE, chr(1), 'x'] + \
            [cn_serial_io.SYNC_BYTE, chr(2), cn_serial_io.SYNC_BYTE, cn_serial_io.SYNC_BYTE]
    result_packets = ['abc', 'x', cn_serial_io.SYNC_BYTE + cn_serial_io.SYNC_BYTE]

    unlock_test = threading.Event()

    def read_mock():
        if read_values == []:
            unlock_test.set()
            raise select.error
        return read_values.pop(0)

    def cb_packet_received(packet):
        assert packet == result_packets.pop(0)

    serial_mock = serial_mock_class.return_value
    serial_mock.read.side_effect = read_mock


    rxtx = cn_serial_io.RxTxSerial(cb_packet_received)
    rxtx.start()

    # wait until read finished
    unlock_test.wait()

    rxtx.stop()

@mock.patch('serial.Serial')
def test_rx_wih_invalid_start(serial_mock_class):

    rx_queue = Queue.Queue(0)

    # configure test
    read_values = ['D', 'D', 'E','K','K'] + \
            [cn_serial_io.SYNC_BYTE, chr(3), 'a', 'b', 'c'] + \
            [cn_serial_io.SYNC_BYTE, chr(1), 'x'] + \
            [cn_serial_io.SYNC_BYTE, chr(2), cn_serial_io.SYNC_BYTE, cn_serial_io.SYNC_BYTE]
    result_packets = ['abc', 'x', cn_serial_io.SYNC_BYTE + cn_serial_io.SYNC_BYTE]

    unlock_test = threading.Event()

    def read_mock():
        if read_values == []:
            unlock_test.set()
            raise select.error
        return read_values.pop(0)

    def cb_packet_received(packet):
        assert packet == result_packets.pop(0)


    serial_mock = serial_mock_class.return_value
    serial_mock.read.side_effect = read_mock

    rxtx = cn_serial_io.RxTxSerial(cb_packet_received)
    rxtx.start()

    # wait until read finished
    unlock_test.wait()

    rxtx.stop()



















