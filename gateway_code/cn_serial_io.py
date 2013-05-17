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



class RxTxSerial(object):
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
                baudrate=baudrate, timeout=0.1)

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
# Disable: I0011 - 'locally disabling warning'
# Disable: C0103 - Invalid name 'Buffer' -> represents a class

Buffer = recordtype.recordtype('Buffer',        #pylint:disable=I0011,C0103
        [('length', None), ('payload', None)])
def empty(self):
    """ Empty current buffer """
    self.length = None
    self.payload = bytearray()
Buffer.empty = empty

class ReceiveThread(Thread):
    """Threaded read"""

    def __init__(self, serial_port, cb_packet_received):
        Thread.__init__(self)
        self.cb_packet_received = cb_packet_received
        self.serial_port = serial_port


    def rx_idle(self, _packet, rx_byte_array):
        """
        Adds the sync byte to the packet and changes the rx_State
        to RX_LEN in order to get the next length byte.
        """
        try:
            index = rx_byte_array.index(SYNC_BYTE)
            del(rx_byte_array[:index+1])
            return self.rx_length

        except ValueError: #pragma: no cover
            del(rx_byte_array[:])
            return self.rx_idle

    def rx_length(self, packet, rx_byte_array):
        """
        'length' byte received, store it into packet
        :return: new state for the state machine
        """
        length = rx_byte_array.pop(0)
        if length == 0:
            return self.rx_idle

        packet.length = length
        return self.rx_payload



    def rx_payload(self, packet, rx_byte_array):
        """
        Adds the received byte to payload.

        If packet complete, change state to PACKET_FULL
        else, keep waiting for bytes
        """
        available = len(rx_byte_array)
        needed    = packet.length - len(packet.payload)

        if available >= needed:
            # packet can be completed
            packet.payload.extend(rx_byte_array[:needed])
            del(rx_byte_array[:needed])

            self.cb_packet_received(str(packet.payload))

            # clean packet
            packet.empty()
            return self.rx_idle
        else:
            packet.payload.extend(rx_byte_array)
            del(rx_byte_array[:])
            return self.rx_payload


    def run(self):
        """
        Read packets from the serial link

        Packet have the format:
            | SYNC  |  LENGTH | DATA |
        """
        packet = Buffer()
        packet.empty() # should be empty before using
        next_fct = self.rx_idle

        while True:
            #call to read will block when no bytes are received
            try:
                rx_str = self.serial_port.read(2048)
            except (select.error, serial.SerialException, OSError, TypeError):
                # All exceptions append at least once during tests
                # The list is empirical and may evolve
                break  # pyserial has been closed


            if rx_str:
                rx_b_array = bytearray(rx_str)
                while len(rx_b_array) != 0:
                    # Putting the bytes received into the packet depending on
                    # the reception state (rx_state)
                    next_fct = next_fct(packet, rx_b_array)

            # else: # timeout, ignore
            #     pass





