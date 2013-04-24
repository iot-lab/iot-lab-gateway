# -*- coding: utf-8 -*-

"""
Serial IO layer for control node
"""
import serial
import select # used for 'select.error'
import atexit

import recordtype # mutable namedtuple (for small classes)
from threading import Thread



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
        # Writes are blocking by default, the port is immediately opened
        # on object creation because the port is given
        # Fail early if it should !

        # timeout is set to != 0, to be able to kill the thread
        # but are ignored in the code
        # if blocking, read does not throw exception on close

        self.serial_port = serial.Serial(port=port, \
                baudrate=baudrate, timeout=1)

        self.rx_thread = None
        self.cb_packet_received = cb_packet_received



    def write(self, data):
        """ Add a header and write the packet to the serial port. """
        tx_packet = self.make_header(data)
        self.serial_port.write(tx_packet)

    def start(self):
        """ Start thread."""
        self.rx_thread = ReceiveThread(self.serial_port, \
                self.cb_packet_received)
        self.serial_port.open()
        self.rx_thread.start()
        atexit.register(self.stop) # cleanup in case of error
        return 0

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
# Buffer to hold a packet while being created
# too simple to do a class

# Disable: I0011 - 'locally disabling warning'
# Disable: C0103 - Invalid name 'Buffer' -> represents a class
Buffer = recordtype.recordtype('Buffer', #pylint:disable=I0011,C0103
        [('length', None), ('payload', "")])
# Tells if the packet is complete
Buffer.is_complete = (lambda self: \
        (self.length is not None) and (self.length == len(self.payload)))



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
                rx_char = self.serial_port.read(1)
            except (select.error, serial.SerialException):
                break  # pyserial has been closed

            if rx_char:
                # Putting the bytes received into the packet depending on the
                # reception state (rx_state)
                rx_state = self.state_machine_dict[rx_state](packet, rx_char)

                if rx_state == RX_PACKET_FULL:

                    self.cb_packet_received(packet.payload)
                    rx_state = RX_IDLE
                    packet = Buffer()
            # else: # timeout, ignore
            #     pass





