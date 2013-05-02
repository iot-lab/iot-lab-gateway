#! /usr/bin/env python

"""
Unit tests for server-rest
Complement the 'integration' tests
"""


from mock import patch

import gateway_code
import unittest

import os
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
STATIC_DIR  = CURRENT_DIR + '/static/' # using the 'static' symbolic link

@patch('gateway_code.flash_firmware.config.STATIC_FILES_PATH', new=STATIC_DIR)
@patch('gateway_code.gateway_manager.CONTROL_NODE_FIRMWARE', \
        STATIC_DIR + 'control_node.elf')
class TestServerRest(unittest.TestCase):
    """
    Cover functions uncovered by unit tests
    """

    @patch('subprocess.Popen')
    @patch('gateway_code.server_rest.run')
    def test_main_function(self, run_mock, mock_popen):
        popen = mock_popen.return_value
        popen.communicate.return_value = (mock_out, mock_err) = ("OUT_MSG", "")
        popen.returncode = mock_ret = 0

        args = ['server_rest.py', 'localhost', '8080']
        import serial
        with patch('serial.Serial') as mock_serial:
            gateway_code.server_rest.main(args)


