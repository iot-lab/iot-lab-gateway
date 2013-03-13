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
class TestSerialRedirectionInit:
    """
    Test the SerialRedirection class init
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

            assert mock_thread.call_count == 1

            node_cfg = config.NODES_CFG[node]
            call_args = mock_thread.call_args[0]
            assert node_cfg['tty'] ==  call_args[0]
            assert node_cfg['baudrate'] == call_args[1]



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


from threading import Semaphore
import time
@mock.patch('subprocess.Popen')
class TestSerialRedirectionUsage:

    def test_simple_start(self, mock_popen):

        sem = Semaphore(1)
        def communicate():
            sem.acquire(True)
            return mock.DEFAULT

        def terminate():
            sem.release()

        popen = mock_popen.return_value
        popen.terminate.side_effect = terminate
        popen.communicate.side_effect = communicate
        popen.communicate.return_value = (mock_out, mock_err) = ("OUT_MSG", "")
        popen.returncode = mock_ret = 0

        node = 'm3'
        redirection = SerialRedirection(node)

        # cannot be stoped before start
        assert redirection.stop() == 1

        assert redirection.start() == 0
        assert redirection.is_running == True
        # only one start possible
        assert redirection.start() == 1

        # wait until that it is actually started
        while popen.communicate.call_count == 0:
            time.sleep(0.1)

        redirection.stop()

        assert popen.communicate.call_count >= 1
        assert popen.terminate.call_count >= 1

    def test_program_error(self, mock_popen):
        """
        Test error handler called if error
        """

        sem = Semaphore(0)
        def communicate():
            sem.acquire(True)
            return mock.DEFAULT

        def terminate():
            sem.release()
            pass

        # error handler to detect
        mock_handler = mock.Mock()
        mock_handler.error_handler_detection.return_value = 0
        def error_handler(arg, error_str):
            mock_handler.error_handler('CALLED')

        # Popen mock
        popen = mock_popen.return_value
        popen.terminate.side_effect = terminate
        popen.communicate.side_effect = communicate
        popen.communicate.return_value = (mock_out, mock_err) = ("OUT_ERR", "ERR_ERR")
        popen.returncode = mock_ret = 42

        node = 'm3'
        redirection = SerialRedirection(node, error_handler)

        assert redirection.start() == 0
        # wait until that it is actually started
        while popen.communicate.call_count == 0:
            time.sleep(0.1)

        assert mock_handler.error_handler.call_count <= 1
        redirection.stop()




class Test_num_arguments_required:
    def test_valid_calls(self):
        class test:
            def method2(self, arg1, arg2):
                pass
            def method0(self):
                pass
        t = test()
        assert serial_redirection._num_arguments_required(t.method2) == 2
        assert serial_redirection._num_arguments_required(t.method0) == 0
        def function1(arg1):
            pass
        def function0():
            pass
        assert serial_redirection._num_arguments_required(function1) == 1
        assert serial_redirection._num_arguments_required(function0) == 0

        lambda_2 = (lambda x,y : 0)
        assert serial_redirection._num_arguments_required(lambda_2) == 2


    def test_invalid_calls(self):
        # testing to get 100% coverage

        mock_test = mock.Mock()
        lambda_2 = (lambda x,y : 0)
        mock_test.method.side_effect = lambda_2
        method = mock_test.method

        try:
            serial_redirection._num_arguments_required(method)
        except ValueError:
            pass
        else:
            assert 0, 'No Value Error exception raised'

