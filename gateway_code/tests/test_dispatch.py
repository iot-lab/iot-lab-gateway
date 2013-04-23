from gateway_code import dispatch
from gateway_code import cn_serial_io
from gateway_code.cn_serial_io import SYNC_BYTE
from mock import MagicMock
import mock
import Queue
import serial
import threading
import select

@mock.patch('serial.Serial')
def test_cb_dispatcher(serial_mock_class):

    unlock_test = threading.Event()


    # configure test
    read_values = [SYNC_BYTE, chr(4), chr(0xFF) + 'a' + 'b' + 'c'] + \
            [SYNC_BYTE, chr(4), chr(0x42) +  'def'] + \
            [SYNC_BYTE, chr(2), chr(0xFF), 'Q']

    result_measures_packets = [chr(0xFF) + 'abc'] + [chr(0xFF) + 'Q']
    result_cn_packets = [chr(0x42) + 'def']

    measures_queue = Queue.Queue(0)
    dis = dispatch.Dispatch(measures_queue, 0xF0)

    # mock queues.put method
    measures_queue.put = MagicMock(name='put')
    dis.queue_control_node.put = MagicMock(name='put')

    # mock serial.read method
    def read_one_val():
        if read_values == []:
            unlock_test.set()
            raise select.error
        return read_values.pop(0)

    def read_mock(val=1):
        res = ''
        for _i in range(0, val):
            res += read_one_val()
        return res
    serial_mock = serial_mock_class.return_value
    serial_mock.read.side_effect = read_mock


    rxtx = cn_serial_io.RxTxSerial(dis.cb_dispatcher)
    rxtx.start()

    # wait until read finished
    unlock_test.wait()



    # check the multiple calls
    cn_calls  = [mock.call(packet) for packet in result_cn_packets]
    measures_calls = [mock.call(packet) for packet in result_measures_packets]
    dis.queue_control_node.put.has_calls(cn_calls)
    dis.queue_control_node.put.has_calls(measures_calls)

    rxtx.stop()


@mock.patch('serial.Serial')
def test_cb_dispatcher_send_cmd(serial_mock_class):

    unlock_test = threading.Event()
    unlock_rx_thread = threading.Event()

    # configure test
    read_values = [SYNC_BYTE, chr(4), chr(0xFF) + 'a' + 'b' + 'c'] + \
            [SYNC_BYTE, chr(4), chr(0x42) +  'def'] + \
            [SYNC_BYTE, chr(2), chr(0xFF), 'Q']

    result_measures_packets = [chr(0xFF) + 'abc'] + [chr(0xFF) + 'Q']
    result_cn_packets = [chr(0x42) + 'def']

    measures_queue = Queue.Queue(0)
    dis = dispatch.Dispatch(measures_queue, 0xF0)
    rxtx = cn_serial_io.RxTxSerial(dis.cb_dispatcher)

    dis.io_write = rxtx.write


    global first_run
    first_run = True

    # mock serial.read method
    def read_one_val():
        if read_values == []:
            unlock_test.set()
            raise select.error
        return read_values.pop(0)

    def read_mock(val=1):
        unlock_rx_thread.wait()
        res = ''
        for _i in range(0, val):
            res += read_one_val()
        return res
    serial_mock = serial_mock_class.return_value
    serial_mock.read.side_effect = read_mock
    serial_mock.write.side_effect = lambda x: unlock_rx_thread.set()


    rxtx.start()

    cn_answer = dis.send_command('A')

    # wait until read finished
    unlock_test.wait()

    assert cn_answer == result_cn_packets[0]

    rxtx.stop()

