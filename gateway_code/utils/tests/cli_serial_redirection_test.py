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


""" test serial_redirection module """

import os
import time
import threading
import signal
import unittest
import mock

from gateway_code.tests import utils
from ..cli import serial_redirection

# pylint <= 1.3
# pylint: disable=too-many-public-methods
# pylint >= 1.4
# pylint: disable=too-few-public-methods


class TestMain(unittest.TestCase):
    """ Main function tests """

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('m3'))
    @mock.patch('signal.pause')
    def test_main_function(self, m_pause):
        """ Test cli.serial_redirection main function

        Run and simulate 'stop' with a Ctrl+C
        """
        m_pause.side_effect = KeyboardInterrupt()

        args = ['serial_redirection.py']
        with mock.patch('sys.argv', args):
            serial_redirection.main()
            self.assertTrue(m_pause.called)

    @mock.patch(utils.READ_CONFIG,
                utils.read_config_mock('a8', linux_open_node_type='a8_m3'))
    @mock.patch('signal.pause')
    def test_open_linux_node(self, m_pause):
        """ Test open Linux node cli.serial_redirection

        Run and simulate 'stop' with a Ctrl+C
        """
        m_pause.side_effect = KeyboardInterrupt()

        args = ['serial_redirection.py']
        with mock.patch('sys.argv', args):
            serial_redirection.main()
            self.assertTrue(m_pause.called)

    @mock.patch(utils.READ_CONFIG, utils.read_config_mock('m3'))
    def test_signal_handling(self):
        # pylint: disable=no-self-use
        """ Test signal handling """
        pid = os.getpid()

        def trigger_signal():
            """ trigger sigterm signal """
            time.sleep(2)
            os.kill(pid, signal.SIGTERM)

        thread = threading.Thread(target=trigger_signal)
        thread.daemon = True
        thread.start()
        args = ['serial_redirection.py']
        with mock.patch('sys.argv', args):
            serial_redirection.main()
