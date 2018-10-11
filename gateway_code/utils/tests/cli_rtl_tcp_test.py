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

import unittest

import mock

from ..cli import rtl_tcp

# pylint <= 1.3
# pylint: disable=too-many-public-methods
# pylint >= 1.4
# pylint: disable=too-few-public-methods


class TestRtlTcpMain(unittest.TestCase):
    """ Main function tests """

    @mock.patch('gateway_code.utils.rtl_tcp.RtlTcp')
    @mock.patch('signal.pause')
    def test_main_function(self, m_pause, m_rtl_class):
        """ Test cli.rtl_tcp main function

        Run and simulate 'stop' with a Ctrl+C
        """
        rtl = m_rtl_class.return_value
        m_pause.side_effect = KeyboardInterrupt()

        args = ['rtl_tcp.py', '50000', '868000000']
        with mock.patch('sys.argv', args):
            rtl_tcp.main()

            self.assertTrue(m_pause.called)
            m_rtl_class.assert_called_with(50000, 868000000)
            self.assertTrue(rtl.start.called)
            self.assertTrue(rtl.stop.called)


class TestRtlTcpParsing(unittest.TestCase):
    """ PARSER tests """

    def test_parser(self):
        """ Test cli.rtl_tcp PARSER """
        opts = rtl_tcp.PARSER.parse_args(['50000', '868000000'])
        self.assertEquals(50000, opts.port)
        self.assertEquals(868000000, opts.frequency)
