import serial
import Queue
#import threading
from threading import Lock, Thread


from gateway_code.gateway_logging import logger

SYNC_BYTE = chr(0x80)

#The port is immediately opened on object creation bevause the port is given.
#No timeout on read timeout=None by dflt
SERIAL_PORT = serial.Serial(port='/dev/ttyFITECO_GWT', baudrate=500000)



#Queue can store 1 item
RX_QUEUE = Queue.Queue(1)
PROTECT_SEND = Lock()


#Definitions for the state machine to monitor the completion progress of
#a packet.
RX_IDLE  = 1
RX_LEN = 2
RX_TYPE = 3
RX_PAYLOAD = 4

#Definitions used to trigger the creation of a new Buffer to receive the packet.
IN_USE = 5
UNUSED = 6




class Buffer(object):
    def __init__(self):
        self.length = None
        self.payload = None

    def __repr__(self):
        result = " length=%s, payload=%s" % \
                ( self.length,  self.payload)
        return result

    def __len__(self):
        return  len(self.length) + len(self.payload)




def rx_idle ():
    """Adds the sync byte to the packet and changes the rx_State
    to RX_LEN in order to get the next length byte."""
    return RX_LEN


def rx_length(packet, rx_char):
    """Puts the legth byte into the packet, changes the rx_state
    to RX_TYPE to get the packet type. """
    packet.length = rx_char
    #rx_state = RX_TYPE
    return RX_PAYLOAD

#def rx_type(packet, rx_char):
    #""" Puts the packet type into the packet, changes the rx_state to
    #RX_PAYLOAD to get the packet data."""
    #packet.pkt_type = rx_char
    ##rx_state = RX_PAYLOAD
    #return RX_PAYLOAD

def rx_payload(packet, rx_char):
    """ Adds the payload bytes, check if the packet is complete
    by comparing the length received and the packet length.  If it is
    puts back the rx_state into RX_IDLE. """
    if packet.payload is None:
        packet.payload = rx_char
    else:
        packet.payload += rx_char

    if len(packet) == packet.length:
        #rx_state = RX_IDLE
        logger.debug("\t rx_payload packet : %s" %(packet))
        return RX_IDLE

    return RX_PAYLOAD


STATE_MACHINE_DICT = {  RX_IDLE: rx_idle,
        RX_LEN : rx_length,
        RX_TYPE: rx_type,
        RX_PAYLOAD: rx_payload,
        }

def receive_packets():
    """
    Read packets from the serial link

    Packet have the format:
    # | SYNC  |  LENGTH | DATA |

    """

    buffer_use = UNUSED
    rx_state = RX_IDLE

    while True:
        #call to read will block when no bytes are received
        rx_bytes = SERIAL_PORT.read()

        #New packet is being received, we get a new buffer
        if buffer_use == UNUSED:
            packet = Buffer()
            buffer_use = IN_USE

        #TODO passer tout ce qui est recu aux fonctions au lieu
        #de passer les char un par un
        for rx_char in rx_bytes:
            #Putting the bytes recived into the packet depending on the
            #reception state (rx_state)
            rx_state = STATE_MACHINE_DICT[rx_state](packet, rx_char)


        if rx_state == RX_IDLE:
            buffer_use = UNUSED
            #packet complete
            try:
                RX_QUEUE.put(packet)

            #TODO : ermplir condition queue full, bloquer sur le put?
            except Queue.Full:
                pass






RX_THREAD = Thread(group=None, target=receive_packets, \
    name='rx_thread', args= (), kwargs={})
RX_THREAD.start()

def make_header(data):
    """
    Create a packet from the data

    :param data: contains 'type', maybe 'ack byte', and 'data payload'
    :type data: string

    :return: a packet with header + data
    """
    length = len(data)
    packet = SYNC_BYTE + chr(length) + data
    return packet




def send_packet(data):
    """
    Send a packet and wait for the answer
    """

    PROTECT_SEND.acquire()

    tx_packet = make_header(data)
    SERIAL_PORT.write(tx_packet)

    rx_packet = RX_QUEUE.get(block=True)
    PROTECT_SEND.release()

    return rx_packet

