#! /usr/bin/env python
# -*- coding:utf-8 -*-

import mock


from gateway_code import envoi
import Queue


@mock.patch('serial.serial')
def test_rx(serial):

    rx_queue = Queue.Queue(0)

    # configure test
    read_values = [ envoie.SYNC_BYTE, chr(3), 'ab', 'c', '']
    result_packets = ['abc']

    serial_mock = serial.return_value
    serial_mock.read.side_effect = lambda: read_values.pop(0)

    # Run thread
    rx_thread = envoie.ThreadRead(rx_queue)
    rx_thread.start()

    rec_l = []
    try:
        while True:
            rx = rx_queue.get(block=True, timeout=2)
            rec_l.append(rx)
    except Queue.empty as error:
        pass

    # cleanup
    rx_thread.join()

    print rec_l, result_packets
    assert rec_l == result_packets











