# -*- coding:utf-8 -*-

""" Interface with the `control node serial program`.

Manage sending commands and receiving messages
"""

import subprocess
from subprocess import PIPE
import Queue
import threading
import os
from os.path import dirname
import stat

from tempfile import NamedTemporaryFile

import atexit
from gateway_code import config
from gateway_code import common


import logging
LOGGER = logging.getLogger('gateway_code')


# use for tests
CONTROL_NODE_INTERFACE_ARGS = []


_OML_XML = '''
<omlc id='{node_id}' exp_id='{exp_id}'>
  <collect url='file:{consumption}' encoding='text'>
    <stream name="consumption" mp="consumption" samples='1' />
  </collect>
  <collect url='file:{radio}' encoding='text'>
    <stream name="radio" mp="radio" samples='1' />
  </collect>
</omlc>
'''

STAT_0666 = (stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP |
             stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)


class ControlNodeSerial(object):
    """
    Class handling the communication with the control node serial program
    """

    def __init__(self):
        self.cn_interface_process = None
        self.reader_thread = None
        self.cn_msg_queue = Queue.Queue(1)
        self.protect_send = threading.Semaphore(1)
        # handler to allow changing it in tests
        self.measures_handler = None

        self.cn_serial_ready = None

        self.oml = {
            'files': {},
            'cfg_file': None
        }

        # cleanup in case of error
        atexit.register(self.stop)

    def start(self, user=None, exp_id=None, _args=None,
              _measures_handler=None):
        """Start control node interface.

        Run `control node serial program` and handle its answers.
        """
        # Reset Queue (== use a new one)
        self.cn_serial_ready = Queue.Queue(0)

        # argument, or current value (for tests) or LOGGER.error
        self.measures_handler = _measures_handler or \
            self.measures_handler or LOGGER.error

        args = [config.CONTROL_NODE_SERIAL_INTERFACE]
        args += ['-t', config.NODES_CFG['gwt']['tty']]
        args += self._config_oml(user, exp_id)

        # add arguments, used by tests
        args += _args or CONTROL_NODE_INTERFACE_ARGS
        self.cn_interface_process = subprocess.Popen(
            args, stderr=PIPE, stdin=PIPE)

        self.reader_thread = threading.Thread(target=self._reader)
        self.reader_thread.start()

        ret = self.cn_serial_ready.get()
        return ret

    def _config_oml(self, user, exp_id):
        """ Create oml config files and folder
        if user and exp_id are given

        Returns the list of parameter to give to the serial interface
        """
        if (user is None) or (exp_id is None):
            return []
        exp_desc = {
            'user': user,
            'exp_id': exp_id,
            'node_id': config.hostname()
            }

        oml_files = {}
        oml_files['consumption'] = config.MEASURES_PATH.format(
            type='consumption', **exp_desc)
        oml_files['radio'] = config.MEASURES_PATH.format(
            type='radio', **exp_desc)

        # XML oml config
        exp_desc.update(oml_files)
        oml_xml_str = _OML_XML.format(**exp_desc)

        # check that the directory exists
        for oml_file in oml_files.itervalues():
            oml_folder = dirname(oml_file)
            if not os.access(oml_folder, os.W_OK):
                LOGGER.error('Cannot write in measure folder: %r', oml_folder)
                raise IOError

        # create empty measures files with 666 permissions (truncate if exists)
        for measure_file_path in oml_files.itervalues():
            open(measure_file_path, "w").close()
            os.chmod(measure_file_path, STAT_0666)

        # create a temporary config file with OML_XML config
        oml_cfg_file = NamedTemporaryFile(suffix='--oml.config')
        oml_cfg_file.write(oml_xml_str)
        oml_cfg_file.flush()

        self.oml['cfg_file'] = oml_cfg_file
        self.oml['files'] = oml_files

        return ['-c', oml_cfg_file.name]

    def stop(self):
        """ Stop control node interface.

        Stop `control node serial program` and answers handler.
        """
        if self.cn_interface_process is not None:
            try:
                self.cn_interface_process.terminate()
            except OSError:
                LOGGER.error('Control node process already terminated')

            self.reader_thread.join()
            self.cn_interface_process = None

        # cleanup oml
        if self.oml['cfg_file'] is not None:
            self.oml['cfg_file'].close()

        for measure_file in self.oml['files'].itervalues():
            try:
                if os.path.getsize(measure_file) == 0:
                    os.unlink(measure_file)
            except OSError:
                pass

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
            self.cn_serial_ready.put(0)

        else:  # control node answer to a command
            try:
                self.cn_msg_queue.put_nowait(answer)
            except Queue.Full:
                LOGGER.error('Control node answer queue full: %r', answer)

    def _reader(self):
        """ Reader thread worker.

        Reads and handle control node answers
        """
        while self.cn_interface_process.poll() is None:
            line = self.cn_interface_process.stderr.readline()
            if line == '':
                break
            self._handle_answer(line.strip())
        else:
            LOGGER.error('Control node serial reader thread ended prematurely')
            self.cn_serial_ready.put(1)  # in case of failure at startup

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
                LOGGER.debug('control_node_cmd: %r', command_args[0])
                self.cn_interface_process.stdin.write(command_str)
                # wait for answer 1 second at max
                answer_cn = self.cn_msg_queue.get(block=True, timeout=1.0)
            except Queue.Empty:  # timeout, answer not got
                answer_cn = None
            except AttributeError:  # write when stdin is None
                LOGGER.error('control_node_serial stdin is None')
                answer_cn = None
            except IOError:
                LOGGER.error('control_node_serial process is terminated')
                answer_cn = None

        LOGGER.debug('control_node_answer: %r', answer_cn)

        return answer_cn
