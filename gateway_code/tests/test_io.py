#! /usr/bin/env python
# -*- coding:utf-8 -*-

import mock


from gateway_code import envoi
import Queue
import serial
import sys


@mock.patch('serial.Serial')
def test_rx_multiple_packets(serial_mock_class):

    rx_queue = Queue.Queue(0)

    # configure test
    read_values = [envoi.SYNC_BYTE, chr(3), 'a', 'b', 'c'] + \
            [envoi.SYNC_BYTE, chr(1), 'x'] + \
            [envoi.SYNC_BYTE, chr(2), envoi.SYNC_BYTE, envoi.SYNC_BYTE]
    result_packets = ['abc', 'x', envoi.SYNC_BYTE + envoi.SYNC_BYTE]

    def read_mock():
        if read_values == []:
            raise ValueError
        return read_values.pop(0)

    serial_mock = serial_mock_class.return_value
    serial_mock.read.side_effect = read_mock

    # Run thread
    rx_thread = envoi.ReceiveThread(rx_queue)
    rx_thread.start()

    rec_l = []
    try:
        for res_packet in result_packets:
            rx = rx_queue.get(block=True, timeout=1)
            assert rx == res_packet
    except Queue.Empty as error: # will happen on timeout
        assert 0

    # cleanup
    rx_thread.join()

@mock.patch('serial.Serial')
def test_rx_wih_invalid_start(serial_mock_class):

    rx_queue = Queue.Queue(0)

    # configure test
    read_values = ['D', 'D', 'E','K','K'] + \
            [envoi.SYNC_BYTE, chr(3), 'a', 'b', 'c'] + \
            [envoi.SYNC_BYTE, chr(1), 'x'] + \
            [envoi.SYNC_BYTE, chr(2), envoi.SYNC_BYTE, envoi.SYNC_BYTE]
    result_packets = ['abc', 'x', envoi.SYNC_BYTE + envoi.SYNC_BYTE]

    def read_mock():
        if read_values == []:
            raise ValueError
        return read_values.pop(0)

    serial_mock = serial_mock_class.return_value
    serial_mock.read.side_effect = read_mock

    # Run thread
    rx_thread = envoi.ReceiveThread(rx_queue)
    rx_thread.start()

    rec_l = []
    try:
        for res_packet in result_packets:
            rx = rx_queue.get(block=True, timeout=1)
            assert rx == res_packet
    except Queue.Empty as error: # will happen on timeout
        assert 0

    # cleanup
    rx_thread.join()



















