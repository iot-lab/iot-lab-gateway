from gateway_code import dispatch
from gateway_code import cn_serial_io
from gateway_code.cn_serial_io import SYNC_BYTE
from mock import MagicMock
import mock
import Queue
import serial
import threading

@mock.patch('serial.Serial')
def test_cb_dispatcher(serial_mock_class):

    unlock_test = threading.Event()


    # configure test
    read_values = [SYNC_BYTE, chr(4), chr(0xFF) + 'a' + 'b' + 'c'] + \
            [SYNC_BYTE, chr(4), chr(0x42) +  'def'] + \
            [SYNC_BYTE, chr(2), chr(0xFF), 'Q']

    result_omlpackets = [chr(0xFF) + 'abc'] + [chr(0xFF) + 'Q']
    result_cnpackets = [chr(0x42) + 'def']

    oml_queue = Queue.Queue(0)
    dis = dispatch.Dispatch(oml_queue, chr(0xF0))

    # mock queues.put method
    oml_queue.put = MagicMock(name='put')
    dis.queue_control_node.put = MagicMock(name='put')

    # mock serial.read method
    def read_mock():
        if read_values == []:
            unlock_test.set()
            raise ValueError
        return read_values.pop(0)
    serial_mock = serial_mock_class.return_value
    serial_mock.read.side_effect = read_mock


    rxtx = cn_serial_io.RxTxSerial(dis.cb_dispatcher)
    rxtx.start()

    # wait until read finished
    unlock_test.wait()



    # check the multiple calls
    cn_calls  = [mock.call(packet) for packet in result_cnpackets]
    oml_calls = [mock.call(packet) for packet in result_omlpackets]
    dis.queue_control_node.put.has_calls(cn_calls)
    dis.queue_control_node.put.has_calls(oml_calls)

    rxtx.stop()


@mock.patch('serial.Serial')
def test_cb_dispatcher_send_cmd(serial_mock_class):

    unlock_test = threading.Event()
    unlock_rx_thread = threading.Event()

    # configure test
    read_values = [SYNC_BYTE, chr(4), chr(0xFF) + 'a' + 'b' + 'c'] + \
            [SYNC_BYTE, chr(4), chr(0x42) +  'def'] + \
            [SYNC_BYTE, chr(2), chr(0xFF), 'Q']

    result_omlpackets = [chr(0xFF) + 'abc'] + [chr(0xFF) + 'Q']
    result_cnpackets = [chr(0x42) + 'def']

    oml_queue = Queue.Queue(0)
    dis = dispatch.Dispatch(oml_queue, chr(0xF0))
    rxtx = cn_serial_io.RxTxSerial(dis.cb_dispatcher)

    dis.io_write = rxtx.write


    global first_run
    first_run = True

    # mock serial.read method
    def read_mock():
        unlock_rx_thread.wait()
        if read_values == []:
            unlock_test.set()
            raise ValueError
        return read_values.pop(0)
    serial_mock = serial_mock_class.return_value
    serial_mock.read.side_effect = read_mock
    serial_mock.write.side_effect = lambda x: unlock_rx_thread.set()


    rxtx.start()

    cn_answer = dis.send_command('A')

    # wait until read finished
    unlock_test.wait()

    assert cn_answer == result_cnpackets[0]

    rxtx.stop()

