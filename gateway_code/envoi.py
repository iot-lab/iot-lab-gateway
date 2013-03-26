import serial
import sys
import time
from Queue import Queue
import pdb
import threading
from threading import Thread, Lock


from gateway_code.gateway_logging import logger

SYNC_BYTE = chr(0x80)

#The port is immediately opened on object creation bevause the port is given.
serial_port = serial.Serial('/dev/ttyFITECO_GWT', 500000, timeout=16)

#Queue can store 1 item
rx_queue = Queue(1)
protect_send = Lock()


#Definitions for the state machine to monitor the completion progress of
#a packet.
RX_IDLE  = 1
RX_LEN = 2
RX_TYPE = 3
RX_PAYLOAD = 4

#Definitions used to trigger the creation of a new Buffer to receive the packet.
IN_USE = 5
UNUSED = 6

rx_state = RX_IDLE


class Buffer():
    def __init__(self):
        self.sync = None
        self.length = None
        self.pkt_type = None
        self.payload = None

    def __repr__(self):
        result = "sync id=%s, length=%s, type=%s, payload=%s" % \
                (self.sync, self.length, self.pkt_type, self.payload)
        return result

    def __len__(self):
        return len(self.sync) + len(self.length) + len(self.pkt_type) + \
                len(self.payload)




def rx_idle (packet, rx_char):
    """Adds the sync byte to the packet and changes the rx_State
    to RX_LEN in order to get the next length byte."""
    if rx_char == SYNC_BYTE:
        packet.sync = SYNC_BYTE
        rx_state = RX_LEN
    return

def rx_length(packet, rx_char):
    """Puts the legth byte into the packet, changes the rx_state
    to RX_TYPE to get the packet type. """
    packet.length = rx_char
    rx_state = RX_TYPE
    return

def rx_type(packet, rx_char):
    """ Puts the packet type into the packet, changes the rx_state to
    RX_PAYLOAD to get the packet data."""
    packet.pkt_type = rx_char
    rx_state = RX_PAYLOAD
    return

def rx_payload(packet, rx_char):
    """ Adds the payload bytes, check if the packet is complete
    by comparing the length received and the packet length.  If it is
    puts back the rx_state into RX_IDLE. """
    if packet.payload is None:
        packet.payload = rx_char
    else:
        packet.payload += rx_char

    if len(packet) == packet.length:
        rx_state = RX_IDLE
        logger.debug("\t rx_payload packet : %s" %(packet))

    return


state_machine_dict = {  RX_IDLE: rx_idle,
                            RX_LEN : rx_length,
                            RX_TYPE: rx_type,
                            RX_PAYLOAD: rx_payload,
                            }

def receive_packet():
    #Lock on the serial link whe
    #SYNC  |  LENGTH | TYPE  | PAYLOAD |

    buffer_use = UNUSED

    while True:
        #call to read will block when no bytes are received
        rx_bytes = serial_port.read()

        #New packet is being received, we get a new buffer
        if buffer_use == UNUSED:
            packet = Buffer()
            buffer_use = IN_USE

        #TODO passer tout ce qui est recu aux fonctions au lieu
        #de passer les char un par un
        for rx_char in rx_bytes:
            #Putting the bytes recived into the packet depending on the
            #reception state (rx_state)
            state_machine_dict[rx_state](packet, rx_char)

        if rx_state == RX_IDLE:
            buffer_use = UNUSED
            #packet complete
            try:
                rx_queue.put(packet)

            #TODO : ermplir condition queue full, bloquer sur le put?
            except Queue.Full:
                pass






RXThread = threading.Thread(group=None, target=receive_packet, \
    name='rx_thread', args= (), kwargs={})
RXThread.start()

def make_header(payload):
    #payload is a string, and we add 2 bytes with
    #elnght and sync byte
    #TYPE  included in payload?
    length = len(payload) + 3

    packet = SYNC_BYTE + str(length) + payload
    return packet




def send_packet(payload):

    protect_send.acquire()

    tx_packet = make_header(payload)
    serial_port.write(tx_packet)

    rx_packet = rx_queue.get(block=True)
    protect_send.release()

    return rx_packet

