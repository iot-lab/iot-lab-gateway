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



class RxTxSerial():
    """ Class managing packet Rx and Tx on the serial link
    Rx made by ReceiveThread, byte by byte.
    Tx add header and write packet to the serial link.
    """

    def __init__(self, cb_packet_received, port='/dev/ttyFITECO_GWT', \
            baudrate=500000 ):
        """
        :param cb_packet_received: callback for when a packet is received
        """
        #Writes are blocking by default,the port is immediately opened
        #on object creation because the port is given, timeout is by dlft
        #set to None therfore waits forever.
        self.serial_port = serial.Serial(port=port, \
                baudrate=baudrate)

        #Starting reciving thread
        self.rx_thread = ReceiveThread(self.serial_port, cb_packet_received)



    def write(self, data):
        """ Add a header and write the packet to the serial port. """
        tx_packet = self.make_header(data)
        self.serial_port.write(tx_packet)

    def start(self):
        """ Start thread."""
        self.rx_thread.start()

    def stop(self):
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
        result = "length=%d, payload=%s" % \
                (self.length,  self.payload)
        return result

    def is_complete(self):
        """
        Returns if the packet is complete
        """
        return (self.length is not None) and (self.length == len(self.payload))



class ReceiveThread(Thread):
    """Threaded read"""

    def __init__(self, serial_port, cb_packet_received):
        Thread.__init__(self)
        self.cb_packet_received = cb_packet_received
        self.serial_port = serial_port

        self.state_machine_dict = {
                RX_IDLE: ReceiveThread.rx_idle,
                RX_LEN : ReceiveThread.rx_length,
                RX_PAYLOAD: ReceiveThread.rx_payload,
                RX_PACKET_FULL: None,
                }



    @staticmethod
    def rx_idle(_packet, rx_char):
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

                self.cb_packet_received(packet.payload)
                rx_state = RX_IDLE
                packet = Buffer()





