# -*- coding:utf-8 -*-


"""
Interface with control_node_serial_interface program

Manage sending commands and receiving answers
"""

from subprocess import Popen, PIPE
import Queue
import threading

import atexit
from gateway_code import config


import logging
LOGGER = logging.getLogger('gateway_code')

def _empty_queue(queue):
    """
    Remove all items in Queue
    """
    while not queue.empty():
        answer = queue.get_nowait()
        LOGGER.debug('Dropped old control node answer: %s', answer[0])

class ControlNodeSerial(object):
    """
    Class handling the communication with the control node serial program
    """

    def __init__(self):
        self.cn_interface_process   = None
        self.reader_thread          = None
        self.control_node_msg_queue = Queue.Queue(1)
        self.protect_send           = threading.Lock()

        # cleanup in case of error
        atexit.register(self.stop)


    def start(self):
        """
        Start control node interface
            Start the control_node_serial_interface and listen for answers
        """

        args = [config.CONTROL_NODE_SERIAL_INTERFACE]
        self.cn_interface_process = Popen(args, stderr=PIPE, stdin=PIPE)

        self.reader_thread = threading.Thread(target=self._reader)
        self.reader_thread.start()


    def stop(self):
        """ Stop control node interface """
        if self.cn_interface_process is not None:
            self.cn_interface_process.terminate()
            self.cn_interface_process = None
            self.reader_thread.join()


    def handle_answer(self, line):
        """
        Handle control node answers
            For errors, print the message
            For command answers, send it to command sender
        """
        answer = line.split(' ')
        if answer[0] == 'error':
            # control node error
            LOGGER.error('Control node error: %d', answer[1])
        else:
            # control node answer to a command
            try:
                self.control_node_msg_queue.put_nowait(answer)
            except Queue.Full:
                LOGGER.error('Control node answer queue full')


    def _reader(self):
        """
        Reader thread worker.
            Reads answers from the control node
        """
        while self.cn_interface_process.poll() is None:
            line = self.cn_interface_process.stderr.readline().strip()
            if line == '':
                break
            self.handle_answer(line)
        else:
            LOGGER.error('Control node serial reader thread ended prematurely')


    def send_command(self, command_list):
        """
        Send a command to control node and wait for an answer
        """
        self.protect_send.acquire()
        # remove existing items (old not treated answers)
        _empty_queue(self.control_node_msg_queue)


        command_str = ' '.join(command_list) + '\n'
        self.cn_interface_process.stdin.write(command_str)

        # wait for answer 1 second
        try:
            answer_cn = self.control_node_msg_queue.get(block=True, timeout=1.0)
        except Queue.Empty: # timeout, answer not got
            answer_cn = None

        self.protect_send.release()
        return answer_cn





