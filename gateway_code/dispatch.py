import Queue
from threading import Lock

class Dispatch():
    OML_PKT_TYPE = chr(0xFF)
    def __init__(self, queue_oml, io_write = None):
        self.queue_oml = queue_oml
        self.queue_control_node = Queue.Queue(1) 
        self.io_write = io_write
        self.protect_send = Lock()
        
    
    def cb_dispatcher(self, packet):
        """ Forwards the packet tot the appropriate queue depending on 
        the packet type """
        #check packet type (first byte)
        if packet[0] == self.OML_PKT_TYPE:
            self.queue_oml.put(packet)
        else:
            self.queue_control_node.put(packet)
            
            
    def send_command(self, data):
        """
        Send a packet and wait for the answer
        """
        self.protect_send.acquire()
        self.io_write(data)
        answer_cn = self.queue_control_node.get(block=True)
        self.protect_send.release()
        return answer_cn
        
        
        
        