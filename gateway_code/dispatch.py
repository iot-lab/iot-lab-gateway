import Queue
from threading import Lock

class Dispatch(object):
    def __init__(self, queue_oml, oml_pkt_type, io_write = None):
        self.oml_pkt_type = oml_pkt_type
        self.queue_oml = queue_oml

        self.queue_control_node = Queue.Queue(1)
        self.io_write = io_write
        self.protect_send = Lock()


    def cb_dispatcher(self, packet):
        """ Forwards the packet tot the appropriate queue depending on
        the packet type """
        # check packet type (first byte)
        # only the first 4 bits
        if (ord(packet[0]) & 0xF0) == ord(self.oml_pkt_type):
            self.queue_oml.put(packet)
        else:
            #put the control node's answer into the queue, unlocking
            #send_command
            self.queue_control_node.put(packet)


    def send_command(self, data):
        """
        Send a packet and wait for the answer
        """
        assert self.io_write is not None, 'io_write should be initialized'
        self.protect_send.acquire()

        # remove existing item (old packet lost on timeout?)
        assert self.queue_control_node.max_size == 1
        # if size > 1, add a loop
        if self.queue_control_node.full():
            self.queue_control_node.get_nowait()

        self.io_write(data)
        #Waits for the control node to answer before unlocking send
        #(unlocked by the callback cb_dispatcher
        try:
            answer_cn = self.queue_control_node.get(block=True, timeout=1.0)
        except Queue.Empty:
            answer_cn = None

        self.protect_send.release()
        return answer_cn




