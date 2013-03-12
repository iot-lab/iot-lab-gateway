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

@mock.patch(_SerialRedirection_str)
class TestSerialRedirection:
    """
    Test the SerialRedirection class
    """

    def test_valid_init(self, mock_thread):
        """
        Test valid init calls
        """
        # Test init and handler_arg
        for node in ('m3', 'gwt', 'a8'):
            mock_thread.reset_mock()

            redirection = SerialRedirection(node)
            assert redirection.node == node
            assert redirection.is_running == False

            print mock_thread.call_count
            assert mock_thread.call_count == 1

            call_args = mock_thread.call_args_list[0][0]
            assert config.NODES_CFG[node]['tty'] ==  call_args[0]
            assert config.NODES_CFG[node]['baudrate'] == call_args[1]


    def test_error_handler_and_arg(self, mock_thread):
        """
        Test calling with an error handler and an argument
        """
        valid_error_handler = (lambda x,y:0)

        redirection = SerialRedirection('m3', valid_error_handler, handler_arg = 'Test')
        assert redirection.error_handler == valid_error_handler
        assert redirection.handler_arg == 'Test'

        assert mock_thread.call_count == 1



    def test_no_error_handler(self, mock_thread):
        """
        Test using without error handler/arg
        """
        redirection = SerialRedirection('m3')
        assert redirection.error_handler is None
        assert redirection.handler_arg is None

        assert mock_thread.call_count == 1



    def test_invalid_init(self, mock_thread):
        """
        Test Invalid init calls
        """
        mock_thread.side_effect = Exception('Should not have been called')

        # invalid node name
        try:
            node = 'FALS_NODE_NAME'
            redirection = SerialRedirection(node)
        except ValueError as error:
            assert re.search('Unknown node', str(error))
        else:
            assert 0

        # invalid error handlers
        try:
            false_error_handler = (lambda x:0)
            redirection = SerialRedirection('m3', false_error_handler)
        except ValueError as error:
            assert re.search('Error handler', str(error))
        else:
            assert 0


    def test_start(self, mock_thread):
        pass

