from gateway_code import dispatch
from gateway_code import cn_serial_io
from mock import MagicMock
import mock
import Queue
import serial
import threading

@mock.patch('serial.Serial')

def test_cb_dispatcher(serial_mock_class):
    # configure test
    payloads_rcvd = [chr(0xFF) + chr(3) + 'abc', \
                'F' + chr(1)+ 'x', chr(0xFF) + chr(2) ] 

    result_omlpackets = [chr(0xFF) + chr(3) + 'abc']
    result_cnpackets = ['F' + chr(1)+ 'x', chr(0xFF) + chr(2)]
    
    unlock_test = threading.Event()
    oml_queue = Queue.Queue(0)
    oml_queue.put = MagicMock(name='put')
    
    dis = dispatch.Dispatch(oml_queue)
    dis.queue_control_node.put = MagicMock(name='put')
    
    def read_mock():
        if payloads_rcvd == []:
            unlock_test.set()
            raise ValueError
        return payloads_rcvd.pop(0)

    serial_mock = serial_mock_class.return_value
    serial_mock.read.side_effect = read_mock
    
    rxtx = cn_serial_io.RxTxSerial(dis.cb_dispatcher)
    rxtx.start()
    
    dis.queue_control_node.put.assert_called_with('F' + chr(1)+ 'x', chr(0xFF) + chr(2))
    oml_queue.put.assert_called_once_with((chr(0xFF) + chr(3) + 'abc'))
    
    # wait until read finished
    unlock_test.wait()

    rxtx.stop()