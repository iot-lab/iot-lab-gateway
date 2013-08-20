#! /usr/bin/env python

"""
Unit tests for server-rest
Complement the 'integration' tests
"""


from mock import patch

import gateway_code
import unittest

import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR  = CURRENT_DIR + '/static/' # using the 'static' symbolic link

# Patch to find idle.elf
# Patch to find control_node.elf at startup
# Patch to find '/var/log/config/board_type' -> tests/config_m3/board_type


MOCK_FIRMWARES = {
    'idle': STATIC_DIR + 'idle.elf',
    'control_node': STATIC_DIR + 'control_node.elf',
    }


@patch('gateway_code.openocd_cmd.config.STATIC_FILES_PATH', new=STATIC_DIR)
@patch('gateway_code.gateway_manager.config.FIRMWARES', MOCK_FIRMWARES)
@patch('gateway_code.config.GATEWAY_CONFIG_PATH', CURRENT_DIR + '/config_m3/')
class TestServerRest(unittest.TestCase):
    """
    Cover functions uncovered by unit tests
    """

    @patch('subprocess.Popen')
    @patch('bottle.run')
    def test_main_function(self, run_mock, mock_popen):
        popen = mock_popen.return_value
        popen.communicate.return_value = (mock_out, mock_err) = ("OUT_MSG", "")
        popen.returncode = mock_ret = 0

        args = ['server_rest.py', 'localhost', '8080']
        gateway_code.server_rest._main(args)


