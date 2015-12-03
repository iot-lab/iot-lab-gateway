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


""" Test utils.ftdi_check """

import textwrap
import unittest
import mock

from ..ftdi_check import ftdi_check


@mock.patch('subprocess.check_output')
class TestFtdiCheck(unittest.TestCase):
    """ Test utils.ftdi_check """

    def test_ftdi_present(self, m_check_output):
        """ Test the 'ftdi_check' method when it is present """

        m_check_output.return_value = textwrap.dedent('''\
            FTx232 devices lister by IoT-LAB
            Listing FT4232 devices...
            Found 1 device(s)
            Device 0:
                Manufacturer: IoT-LAB
                Description: ControlNode
                Serial:
            All done, success!
            ''')
        self.assertEquals(0, ftdi_check('control', '4232'))
        m_check_output.assert_called_with(['ftdi-devices-list', '-t', '4232'])

    def test__ftdi_is_absent(self, m_check_output):
        """ Test the 'ftdi_check' method when it is absent """
        m_check_output.return_value = textwrap.dedent('''\
            FTx232 devices lister by IoT-LAB
            Listing FT2232 devices...
            No FTDI device found
            All done, success!
            ''')
        self.assertEquals(1, ftdi_check('open', '2232'))
        m_check_output.assert_called_with(['ftdi-devices-list', '-t', '2232'])
