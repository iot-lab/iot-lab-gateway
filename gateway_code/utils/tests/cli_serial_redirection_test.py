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

import mock
import unittest

from ..cli import serial_redirection

# pylint <= 1.3
# pylint: disable=too-many-public-methods
# pylint >= 1.4
# pylint: disable=too-few-public-methods


class TestMain(unittest.TestCase):
    """ Main function tests """

    @mock.patch('gateway_code.utils.serial_redirection.SerialRedirection')
    @mock.patch('signal.pause')
    def test_main_function(self, m_pause, m_serial_redirect_class):
        """ Test cli.serial_redirection main function

        Run and simulate 'stop' with a Ctrl+C
        """
        redirect = m_serial_redirect_class.return_value
        m_pause.side_effect = KeyboardInterrupt()

        args = ['serial_redirection.py', '/dev/ttyON_M3', '500000']
        with mock.patch('sys.argv', args):
            serial_redirection.main()

            self.assertTrue(m_pause.called)
            m_serial_redirect_class.assert_called_with('/dev/ttyON_M3', 500000)
            self.assertTrue(redirect.start.called)
            self.assertTrue(redirect.stop.called)


class TestArgumentsParsing(unittest.TestCase):
    """ PARSER tests """

    def test_parser(self):
        """ Test cli.serial_redirection PARSER """
        opts = serial_redirection.PARSER.parse_args(['tty', '500000'])
        self.assertEquals('tty', opts.tty)
        self.assertEquals(500000, opts.baudrate)
