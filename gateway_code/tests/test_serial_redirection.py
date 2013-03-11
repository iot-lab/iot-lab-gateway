#! /usr/bin/env python
# -*- coding:utf-8 -*-

if __name__ == '__main__':
    import sys
    sys.path.append("../../")


from gateway_code import serial_redirection
from gateway_code import config

import mock
import re

_SerialRedirection_str = 'gateway_code.serial_redirection._SerialRedirectionThread'

from gateway_code.serial_redirection import SerialRedirection
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
                assert re.search('Unknown node', error.message)
            else:
                assert 0

            try:
                node = 'm3'
                def false_error_handler(only_one_arg):
                    pass
                redirection = SerialRedirection(node, false_error_handler)
            except ValueError as error:
                assert re.search('Error handler', error.message)
            else:
                assert 0


    def test_start(self):
        pass











#@mock.patch('subprocess.Popen', common.PopenMock)
# class Test_SerialRedirectionThread:
#     """
#     Tests the private _SerialRedirectionThread class
#     """
# 
#     def test_init(self):
#         """
#         Test Object creation
#         """
# 
#         node = 'm3'
#         def __error_handler_one_arg(error_str):
#             pass
#         error_handler = __error_handler_one_arg
# 
#         redirect_thread = serial_redirection._SerialRedirectionThread(\
#                 tty, baudrate, error_handler)
#         assert redirect_thread.tty == tty
#         assert redirect_thread.baudrate == baudrate
#         assert redirect_thread.error_handler == error_handler



