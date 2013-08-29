# -*- coding:utf-8 -*-

""" Interface with the `control node serial program`.

Manage sending commands and receiving messages
"""

import subprocess
from subprocess import PIPE
import Queue
import threading

import atexit
from gateway_code import config
from gateway_code import common


import logging
LOGGER = logging.getLogger('gateway_code')


# use for tests
CONTROL_NODE_INTERFACE_ARGS = []


class ControlNodeSerial(object):
    """
    Class handling the communication with the control node serial program
    """

    def __init__(self):
        self.cn_interface_process = None
        self.reader_thread = None
        self.cn_msg_queue = Queue.Queue(1)
        self.protect_send = threading.Semaphore(1)

        # cleanup in case of error
        atexit.register(self.stop)

    def start(self):
        """Start control node interface.

        Run `control node serial program` and handle its answers.
        """

        args = [config.CONTROL_NODE_SERIAL_INTERFACE]
        args += ['-t', config.NODES_CFG['gwt']['tty']]
        args += CONTROL_NODE_INTERFACE_ARGS
        self.cn_interface_process = subprocess.Popen(
            args, stderr=PIPE, stdin=PIPE)

        self.reader_thread = threading.Thread(target=self._reader)
        self.reader_thread.start()

    def stop(self):
        """ Stop control node interface.

        Stop `control node serial program` and answers handler.
        """
        if self.cn_interface_process is not None:
            self.cn_interface_process.terminate()
            self.reader_thread.join()
            self.cn_interface_process = None

    def _handle_answer(self, line):
        """Handle control node answers

          * For errors, print the message
          * For command answers, send it to command sender
        """
        answer = line.split(' ')
        if answer[0] == 'config_ack':  # ack reset_time/measures
            LOGGER.debug('config_ack %s', answer[1])
        elif answer[0] == 'error':  # control node error
            LOGGER.error('Control node error: %r', answer[1])

        # debug messages
        elif answer[0] == 'cn_serial_error:':  # control node serial error
            LOGGER.error(line)
        elif answer[0] == 'measures_debug:':  # measures output
            LOGGER.debug(line)

        else:  # control node answer to a command
            try:
                self.cn_msg_queue.put_nowait(answer)
            except Queue.Full:
                LOGGER.error('Control node answer queue full')

    def _reader(self):
        """ Reader thread worker.

        Reads and handle control node answers
        """
        while self.cn_interface_process.poll() is None:
            line = self.cn_interface_process.stderr.readline().strip()
            if line == '':
                break
            self._handle_answer(line)
        else:
            LOGGER.error('Control node serial reader thread ended prematurely')

    def send_command(self, command_args):
        """ Send given command to control node and wait for an answer

        :param command_args: command arguments
        :type command_args: list of string
        :return: received answers or `None` if timeout caught
        """
        command_str = ' '.join(command_args) + '\n'
        with self.protect_send:
            # remove existing items (old not treated answers)
            common.empty_queue(self.cn_msg_queue)
            try:
                self.cn_interface_process.stdin.write(command_str)
                # wait for answer 1 second at max
                answer_cn = self.cn_msg_queue.get(block=True, timeout=1.0)
            except Queue.Empty:  # timeout, answer not got
                answer_cn = None

        return answer_cn
