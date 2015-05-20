# -*- coding:utf-8 -*-

""" Test utils.ftdi_check """

import unittest
import mock
import textwrap

from ..ftdi_check import ftdi_check


@mock.patch('subprocess.check_output')
class TestFtdiCheck(unittest.TestCase):
    """ Test utils.ftdi_check """

    def test__ftdi_is_present(self, m_check_output):
        """ Test the '_ftdi_is_present' method """

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

        m_check_output.return_value = textwrap.dedent('''\
            FTx232 devices lister by IoT-LAB
            Listing FT2232 devices...
            No FTDI device found
            All done, success!
            ''')
        self.assertEquals(1, ftdi_check('open', '2232'))
        m_check_output.assert_called_with(['ftdi-devices-list', '-t', '2232'])
