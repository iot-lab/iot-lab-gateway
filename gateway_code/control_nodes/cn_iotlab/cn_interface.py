# -*- coding:utf-8 -*-

# This file is a part of IoT-LAB gateway_code
# Copyright (C) 2015 INRIA (Contact: admin@iot-lab.info)
# Contributor(s) : see AUTHORS file
#
# This software is governed by the CeCILL license under French law
# and abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# http://www.cecill.info.
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.


""" Interface with the `control node serial program`.

Manage sending commands and receiving messages
"""

import queue
import sys
import threading
import logging
import atexit

from subprocess import PIPE
from tempfile import NamedTemporaryFile

from gateway_code import common
from gateway_code.utils import subprocess_timeout

# There are encoding issues with Python 3.5
PY35 = sys.version_info.major == 3 and sys.version_info.minor == 5

LOGGER = logging.getLogger('gateway_code')


CONTROL_NODE_SERIAL_INTERFACE = 'control_node_serial_interface'


OML_XML = '''
<omlc id='{node_id}' exp_id='{exp_id}'>
  <collect url='file:{consumption}' encoding='text'>
    <stream name="consumption" mp="consumption" samples='1' />
  </collect>
  <collect url='file:{radio}' encoding='text'>
    <stream name="radio" mp="radio" samples='1' />
  </collect>
  <collect url='file:{event}' encoding='text'>
    <stream name="event" mp="event" samples='1' />
  </collect>
  <collect url='file:{sniffer}' encoding='text'>
    <stream name="sniffer" mp="sniffer" samples='1' />
  </collect>
</omlc>
'''


class ControlNodeSerial(object):  # pylint:disable=too-many-instance-attributes
    """
    Class handling the communication with the control node serial program
    """

    def __init__(self, tty):
        self.tty = tty
        self.process = None
        self.reader_thread = None
        self.msgs = queue.Queue(1)
        self.measures_debug = None

        self._send_mutex = threading.Semaphore(1)
        self._wait_ready = queue.Queue(1)
        self._oml_cfg_file = None

        # cleanup in case of error
        atexit.register(self.stop)

    def start(self, oml_xml_config=None):
        """Start control node interface.

        Run `control node serial program` and handle its answers.
        """
        common.empty_queue(self._wait_ready)

        args = self._cn_interface_args(oml_xml_config)
        self.process = subprocess_timeout.Popen(args, stderr=PIPE, stdin=PIPE)

        self.reader_thread = threading.Thread(target=self._reader)
        self.reader_thread.start()

        ret = self._wait_ready.get()
        return ret

    def _cn_interface_args(self, oml_xml_config=None):
        """ Arguments for control_node_serial_interface """
        args = [CONTROL_NODE_SERIAL_INTERFACE, '-t', self.tty]

        # OML Configuration
        self._oml_cfg_file = self._oml_config_file(oml_xml_config)
        if self._oml_cfg_file is not None:
            args += ['-c', self._oml_cfg_file.name]

        # Debug mode
        if self.measures_debug is not None:
            args += ['-d']

        return args

    @staticmethod
    def _oml_config_file(oml_xml_config=None):
        """ Create oml config file """

        # empty description for autotests
        if oml_xml_config is None:
            return None

        # Save xml configuration in a temporary file
        cfg_file = NamedTemporaryFile(suffix='--oml.config')
        cfg_file.write(oml_xml_config.encode())
        cfg_file.flush()

        return cfg_file

    @staticmethod
    def oml_xml_config(node_id, exp_id, exp_files_dict=None):
        """ Generate the oml xml configuration """
        if not exp_files_dict:
            return None
        cfg = OML_XML.format(node_id=node_id, exp_id=exp_id, **exp_files_dict)
        return cfg.strip()

    def stop(self):
        """ Stop control node interface.

        Stop `control node serial program` and answers handler.  """

        try:
            self._process_stop(timeout=5)
        except OSError:
            LOGGER.error('Control node process already terminated')

        if self.reader_thread is not None:
            self.reader_thread.join()

        # remove process after reader_thread is joined
        self.process = None
        self.measures_debug = None

        # cleanup oml
        if self._oml_cfg_file is not None:
            self._oml_cfg_file.close()
            self._oml_cfg_file = None
        return 0

    def _process_stop(self, timeout=None):
        """Stop or kill control node interface.

        :raises: OSError if already terminated
        """
        try:
            LOGGER.debug('Control node serial process terminate')
            self.process.terminate()
            self.process.wait(timeout=timeout)
        except subprocess_timeout.TimeoutExpired:
            # may not have been killed sometime
            LOGGER.warning('Control node serial not terminated, kill it')
            self.process.kill()
        except AttributeError:
            pass  # None

    def _handle_answer(self, line):
        """Handle control node answers

          * For errors, print the message
          * For command answers, send it to command sender
        """
        answer = line.split(' ')
        if answer[0] == 'config_ack':  # ack set_time/measures
            LOGGER.debug('config_ack %s', answer[1])
            if answer[1] == 'set_time':
                LOGGER.info('Control Node set time delay: %d us',
                            int(1000000 * float(answer[2])))
        elif answer[0] == 'error':  # control node error
            LOGGER.error('Control node error: %r', answer[1])

        # debug messages
        elif answer[0] == 'cn_serial_error:':  # control node serial error
            LOGGER.error(line)
        elif answer[0] == 'measures_debug:':  # measures output
            self.measures_handler(line)
        elif answer[0] == 'cn_serial_ready':  # cn_serial interface ready
            self._wait_ready.put(0)

        else:  # control node answer to a command
            try:
                self.msgs.put_nowait(answer)
            except queue.Full:
                LOGGER.error('Control node answer queue full: %r', answer)

    def measures_handler(self, line):
        """ Debug measures """
        LOGGER.debug(line)
        if self.measures_debug is not None:
            self.measures_debug(line)  # pylint:disable=not-callable

    def _reader(self):
        """ Reader thread worker.

        Reads and handle control node answers
        """
        while self.process.poll() is None:
            if PY35:
                line = self.process.stderr.readline().decode().strip()
            else:
                line = self.process.stderr.readline().strip()
            if line == '':
                break
            self._handle_answer(line)
        else:
            LOGGER.error('Control node serial reader thread ended prematurely')
            self._wait_ready.put(1)  # in case of failure at startup

    def send_command(self, command_args):
        """ Send given command to control node and wait for an answer

        :param command_args: command arguments
        :type command_args: list of string
        :return: received answers or `None` if timeout caught
        """
        command_str = ' '.join(command_args) + '\n'
        with self._send_mutex:
            # remove existing items (old not treated answers)
            common.empty_queue(self.msgs)
            try:
                self.process.stdin.write(command_str.encode())
                self.process.stdin.flush()
                # wait for answer 1 second at max
                answer_cn = self.msgs.get(block=True, timeout=1.0)
            except queue.Empty:
                LOGGER.error('control_node_serial answer timeout')
                answer_cn = None
            except AttributeError:
                LOGGER.error('control_node_serial stdin is None')
                answer_cn = None
            except IOError:
                LOGGER.error('control_node_serial process is terminated')
                answer_cn = None
            finally:
                LOGGER.debug('control_node_answer: %r', answer_cn)

        return answer_cn
