# -*- coding: utf-8 -*-

"""
Serial IO layer for control node
"""
import serial
from threading import  Thread


# Remove for the moment
#  from gateway_code.gateway_logging import logger

SYNC_BYTE = chr(0x80)





# States of the packet reception progression state machine.
RX_IDLE, RX_LEN, RX_PAYLOAD, RX_PACKET_FULL = range(4)

#Definitions used to trigger the creation of a new Buffer to receive the packet.
IN_USE = 5
UNUSED = 6


class RxTxSerial():
    """ Class managing packet Rx and Tx on the serial link
    Rx made by ReceiveThread, byte by byte. Tx is reduced to writing the packet
    to the serial link.
     """
    
    def __init__(self, cb_dispatch):
        """:cb_dispatch Manager callback to dispatch packets to 
        the appropriate upper layer depending on their type 
        (from control node or OML)
        """
        #Writes are blocking by default,the port is immediately opened 
        #on object creation because the port is given, timeout is by dlft
        #set to None therfore waits forever.
        self.serial_port = serial.Serial(port='/dev/ttyFITECO_GWT', \
                baudrate=500000)
                
        #Starting reciving thread       
        self.rx_thread = ReceiveThread(self.serial_port, cb_dispatch)
        self.rx_thread.start()

        
    def write(self, tx_packet):
        """ Writes the packet to the serial port. """
        self.serial_port.write(tx_packet)
        
            
    def stop_rx_thread(self):
        """Stops receive thread by closing the serial port, Wait for the 
        thread to exit with a call to join().
        """
        self.serial_port.close()
        self.rx_thread.join()
        
        
    @staticmethod   
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
     
     
class Buffer(object):
    """
    Buffer to hold a packet while being created
    """

    def __init__(self):
        self.length = None
        self.payload = ""

    def __repr__(self):
        result = " length=%d, payload=%s" % \
                ( self.length,  self.payload)
        return result

    def is_complete(self):
        """
        Returns if the packet is complete
        """
        return (self.length is not None) and (self.length == len(self.payload))



class ReceiveThread(Thread):
    """Threaded read"""
    def __init__(self, serial_port, cb_dispatch ):
        Thread.__init__(self)
        self.cb_dispatch = cb_dispatch
        self.serial_port = serial_port
        self.state_machine_dict = {}
           
      
    
    @staticmethod
    def rx_idle(packet, rx_char):
        """
        Adds the sync byte to the packet and changes the rx_State
        to RX_LEN in order to get the next length byte.
        """
        if rx_char == SYNC_BYTE:
            return RX_LEN
        else:
            #logger.debug("rx_idle : packet lost?")
            return RX_IDLE
    
    @staticmethod
    def rx_length(packet, rx_char):
        """
        'length' byte received, store it into packet
        :return: new state for the state machine
        """
    
        packet.length = ord(rx_char)
        return RX_PAYLOAD
    
    @staticmethod
    def rx_payload(packet, rx_char):
        """
        Adds the received byte to payload.
    
        If packet complete, change state to PACKET_FULL
        else, keep waiting for bytes
        """
        packet.payload += rx_char
    
        if packet.is_complete():
            #logger.debug("\t rx_payload packet : %s" %(packet))
            return RX_PACKET_FULL
    
        return RX_PAYLOAD
    
    

      
    def run(self):
        """
        Read packets from the serial link

        Packet have the format:
            | SYNC  |  LENGTH | DATA |
        """

        rx_state = RX_IDLE
        packet = Buffer()
        self.state_machine_dict =  {RX_IDLE: ReceiveThread.rx_idle,
            RX_LEN : ReceiveThread.rx_length,
            RX_PAYLOAD: ReceiveThread.rx_payload,
            RX_PACKET_FULL: None,
            }  
        while True:
            #call to read will block when no bytes are received
            try:
                rx_char = self.serial_port.read()
            except ValueError:
                break

            # Putting the bytes received into the packet depending on the
            # reception state (rx_state)
            rx_state = self.state_machine_dict[rx_state](packet, rx_char)


            if rx_state == RX_PACKET_FULL:
                
                self.cb_dispatch(packet.payload)
              
                rx_state = RX_IDLE
                packet = Buffer()
            




#def send_packet(data):
    #"""
    #Send a packet and wait for the answer
    #"""

    #self.protect_send.acquire()

    #tx_packet = make_header(data)
    #SERIAL_PORT.write(tx_packet)

    #rx_packet = RX_QUEUE.get(block=True)
    #self.protect_send.release()

    #return rx_packet

