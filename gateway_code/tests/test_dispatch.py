# -*- coding:utf-8 -*-
from gateway_code import dispatch, cn_serial_io
from gateway_code.cn_serial_io import SYNC_BYTE

from mock import MagicMock
import mock
import unittest

import Queue
import threading
import serial
import time


class TestDispatch(unittest.TestCase):

    def setUp(self):
        self.unlock_test = threading.Event()

        self.serial_patcher = mock.patch('serial.Serial')
        serial_class_mock   = self.serial_patcher.start()
        serial_mock         = serial_class_mock.return_value
        self.serial_mock    = serial_mock

        serial_mock.read.side_effect  = self._read_mock
        def mock_close():
            serial_mock.read.side_effect = serial.SerialException
        serial_mock.close.side_effect = mock_close

        self.measures_queue = Queue.Queue(0)
        self.dis            = dispatch.Dispatch(self.measures_queue, 0xF0)
        self.rxtx           = cn_serial_io.RxTxSerial(self.dis.cb_dispatcher)
        self.dis.io_write   = self.rxtx.write

    def tearDown(self):
        self.serial_patcher.stop()
        self.rxtx.stop() # cleanup on error

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



    def test_cb_dispatcher(self):
        """
        Test cb_dispatcher callback

        Write bytes on 'serial' interface and see that the output is correct
        """

        # configure test
        self.read_values = [SYNC_BYTE, chr(4), chr(0xFF), 'a', 'b', 'c'] + \
                [SYNC_BYTE, chr(4), chr(0x42), 'd', 'e', 'f'] + \
                [SYNC_BYTE, chr(2), chr(0xFD), 'Q']

        self.result_measures_packets = [chr(0xFF) + 'abc'] + [chr(0xFD) + 'Q']
        self.result_cn_packets = [chr(0x42) + 'def']

        # replace Queue with an infinite queue
        self.dis.queue_control_node = Queue.Queue(0)
        self.rxtx.start()

        self.unlock_test.wait()     # wait until read finished

        self.rxtx.stop()

        # check received packets
        for result_measure in self.result_measures_packets:
            self.assertEquals(result_measure, self.measures_queue.get_nowait())
        for result_measure in self.result_cn_packets:
            self.assertEquals(result_measure, self.dis.queue_control_node.get_nowait())



    def test_cb_dispatcher_send_cmd(self):

        unlock_rx_thread = threading.Event()

        # configure test
        self.read_values = [SYNC_BYTE, chr(4), chr(0xFF), 'a', 'b', 'c'] + \
                [SYNC_BYTE, chr(4), chr(0x42), 'd', 'e', 'f'] + \
                [SYNC_BYTE, chr(4), chr(0x42), 'g', 'h', 'i'] + \
                [SYNC_BYTE, chr(2), chr(0xFF), 'Q']

        self.result_measures_packets = [chr(0xFF) + 'abc'] + [chr(0xFF) + 'Q']
        self.result_cn_packets = [chr(0x42) + 'def'] # second packet is not awaited


        def read_mock(val=1):
            unlock_rx_thread.wait()
            return self._read_mock(val)
        self.serial_mock.read.side_effect = read_mock
        self.serial_mock.write.side_effect = lambda x: unlock_rx_thread.set()

        # old remaining packet in the queue should be removed
        self.dis.queue_control_node.put('OLD_PACKET')

        self.rxtx.start()

        cn_answer = self.dis.send_command('A')

        self.unlock_test.wait()
        self.rxtx.stop()


        self.assertEquals(cn_answer, self.result_cn_packets[0])
        for result_measure in self.result_measures_packets:
            self.assertEquals(result_measure, self.measures_queue.get_nowait())



    def test_control_node_timeout_and_measure_queue_full(self):
        """
        test_control_node_timeout_and_measure_queue_full

        Send a command with no answer from control node
        Put too many packets in the measure_queue
        """

        # configure test
        self.read_values = [SYNC_BYTE, chr(4), chr(0xFF), 'a', 'b', 'c'] + \
                [SYNC_BYTE, chr(2), chr(0xFF), 'Q']
                # no result packet

        self.result_measures_packets = [chr(0xFF) + 'abc']
        # second packet is droped due to queue full

        # replace queue with a limited queue to force 'Queue.Full'
        self.measures_queue = Queue.Queue(1)
        self.dis.measures_queue = self.measures_queue

        self.rxtx.start()
        cn_answer = self.dis.send_command('A')
        self.unlock_test.wait()
        self.rxtx.stop()

        # checks received packets
        self.assertEquals(cn_answer, None) # timeout
        for result_measure in self.result_measures_packets:
            self.assertEquals(result_measure, self.measures_queue.get_nowait())
        self.assertRaises(Queue.Empty, self.measures_queue.get_nowait)



