#! /usr/bin/env python
# -*- coding:utf-8 -*-

import mock
import re
import sys

# import package code from source folder if not installed
from os.path import dirname, abspath
current_folder = dirname(abspath(__file__))
source_folder = dirname(dirname(current_folder))
sys.path.append(source_folder)

from gateway_code.serial_redirection import SerialRedirection
from gateway_code import serial_redirection, config

_SerialRedirection_str = 'gateway_code.serial_redirection._SerialRedirectionThread'

class TestSerialRedirection:
    """
    Test the SerialRedirection class
    """

    def test_valid_init(self):
        """
        Test valid init calls
        """
        # Test init and handler_arg
        for node in ('m3', 'gwt', 'a8'):
            with mock.patch(_SerialRedirection_str) as mock_thread:
                redirection = SerialRedirection(node)
                assert redirection.node == node
                assert redirection.is_running == False
                # check calls to _SerialRedirectionThread
                call_args = mock_thread.call_args_list
                assert len(call_args) == 1
                args = call_args[0][0]
                assert config.NODES_CFG[node]['tty'] ==  args[0]
                assert config.NODES_CFG[node]['baudrate'] == args[1]


        # Test the error handler and handler_arg
        with mock.patch(_SerialRedirection_str) as mock_thread:
            def valid_error_handler(error_num, error_str):
                pass
            redirection = SerialRedirection(node, valid_error_handler, handler_arg = 'Test')
            assert redirection.error_handler == valid_error_handler
            assert redirection.handler_arg == 'Test'

            redirection = SerialRedirection(node)
            assert redirection.error_handler is None
            assert redirection.handler_arg is None



    def test_invalid_init(self):
        """
        Test Invalid init calls
        """
        with mock.patch(_SerialRedirection_str) as mock_thread:
            mock_thread.side_effect = Exception('Called with invalid args')
            try:
                node = 'FALS_NODE_NAME'
                redirection = SerialRedirection(node)
            except ValueError as error:
                assert re.search('Unknown node', str(error))
            else:
                assert 0

            try:
                node = 'm3'
                def false_error_handler(only_one_arg):
                    pass
                redirection = SerialRedirection(node, false_error_handler)
            except ValueError as error:
                assert re.search('Error handler', str(error))
            else:
                assert 0


    def test_start(self):
        pass

