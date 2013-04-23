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

def _wait_call_count_not_null(mock_method, max_wait):
    """
    Wait for at max 'time' seconds that mock_method get called
    :param mock_method: mock method to wait on
    :param max_mait: time to wait at max in seconds

    """
    import time

    steps = 0.1
    num_iteration = int(max_wait / steps)

    for i in range(0, num_iteration):
        if mock_method.communicate.call_count != 0:
            break
        time.sleep(steps)
    else:
        assert mock_method.call_count != 0

@mock.patch(_SerialRedirection_str)
class TestSerialRedirectionInit(object):
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

    def test_error_handler_and_arg(self, mock_thread):
        """
        Test calling with an error handler and an argument
        """
        valid_error_handler = (lambda x,y:0)

        redirection = SerialRedirection('m3', valid_error_handler, handler_arg = 'Test')
        assert redirection.error_handler == valid_error_handler
        assert redirection.handler_arg == 'Test'


    def test_no_error_handler(self, mock_thread):
        """
        Test using without error handler/arg
        """
        redirection = SerialRedirection('m3')
        assert redirection.error_handler is None
        assert redirection.handler_arg is None

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

from cStringIO import StringIO
captured_err = StringIO()
@mock.patch('sys.stderr', captured_err)
@mock.patch('subprocess.Popen')
class TestMainFunction(object):

    def test_simple_start(self, mock_popen):

        sem = Semaphore(0)
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
        ret = redirection.stop()
        assert ret == 1

        ret = redirection.start()
        assert ret == 0
        assert redirection.is_running == True
        # only one start possible
        ret = redirection.start()
        assert ret == 1

        _wait_call_count_not_null(popen.communicate, 1)

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

        ret = redirection.start()
        assert ret == 0
        _wait_call_count_not_null(popen.communicate, 1)

        assert mock_handler.error_handler.call_count <= 1
        redirection.stop()


    @mock.patch('gateway_code.serial_redirection.SerialRedirection')
    def test_error_with_start_redirection(self, mock_open, mock_serial):
        mock_redirection = mock_serial.return_value
        mock_redirection.start.return_value = 1
        try:
            serial_redirection.main(['serial_redirection.py', 'm3'])
        except SystemExit as ret:
            assert ret.code == 1
        else:
            assert 0



    def test_error_on_communicate(self, mock_popen):
        """
        Communicate error that runs main cb_error_handler
        """
        def communicate():
            return mock.DEFAULT
        def terminate():
            pass

        popen = mock_popen.return_value
        popen.terminate.side_effect = terminate
        popen.communicate.side_effect = communicate
        popen.communicate.return_value = (mock_out, mock_err) = ("OUT_MSG", "ERR_MSG")
        popen.returncode = mock_ret = 42

        node = 'm3'
        args = ['serial_redirection.py', node]
        serial_redirection.main(args)



    def test_simple_case(self, mock_popen):

        # stub Popen
        sem = Semaphore(0)
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

        def wait_mock():
            """
            'wait' will call the ctrl+c handler has if a ctrl+c was got
            """
            import signal
            handler = signal.getsignal(signal.SIGINT)
            handler(None, None)

        with mock.patch('gateway_code.serial_redirection.Event') as mock_event:
            event = mock_event.return_value
            event.wait.side_effect = wait_mock

            serial_redirection.main(['serial_redirection.py', 'm3'])
            assert event.wait.call_count == 1



from cStringIO import StringIO
captured_err = StringIO()
@mock.patch('sys.stderr', captured_err)
@mock.patch('subprocess.Popen')
class TestSerialRedirection(object):

    def test_run_with_handler_none(self, mock_popen):
        """
        Communicate error no error handler
        """
        def communicate():
            return mock.DEFAULT
        def terminate():
            pass

        popen = mock_popen.return_value
        popen.terminate.side_effect = terminate
        popen.communicate.side_effect = communicate
        popen.communicate.return_value = (mock_out, mock_err) = ("OUT_MSG", "ERR_MSG")
        popen.returncode = mock_ret = 42

        redirect = serial_redirection.SerialRedirection('m3')
        redirect.start()
        _wait_call_count_not_null(popen.communicate, 2)
        redirect.stop()





from gateway_code.serial_redirection import _SerialRedirectionThread
@mock.patch('subprocess.Popen')
class TestSerialRedirectionThread(object):

    def test_wrong_parameters_init(self, _mock_popen):

        # to get 100% coverage
        # other cases treated by other test suites
        bad_error_handler = (lambda a, b: 0)
        try:
            _SerialRedirectionThread('tty_file', 500000, bad_error_handler)
        except ValueError as e:
            pass
        else:
            assert 0, "No exception raised"

    def test_handler_none(self, mock_popen):
        def communicate():
            return mock.DEFAULT
        def terminate():
            pass

        popen = mock_popen.return_value
        popen.terminate.side_effect = terminate
        popen.communicate.side_effect = communicate
        popen.communicate.return_value = (mock_out, mock_err) = ("OUT_MSG", "ERR_MSG")
        popen.returncode = mock_ret = 42

        redirect = _SerialRedirectionThread('tty_file', 500000, error_handler=None)
        redirect.start()
        _wait_call_count_not_null(popen.communicate, 1)
        redirect.stop()


    def test_terminate_on_non_started_process(self, mock_popen):
        """
        Test terminate with self.redirector_process is None
        """

        # Start thread
        # blocks on Popen
        # run stop
        # sigalarm unlocks popen so that terminate will work on next call

        import signal

        # stub Popen
        sem = Semaphore(0)

        def communicate():
            mock_popen.side_effect = None
            sem.acquire(True)
            return mock.DEFAULT

        def terminate():
            sem.release()

        popen = mock_popen.return_value
        popen.terminate.side_effect = terminate
        popen.communicate.side_effect = communicate
        popen.communicate.return_value = (mock_out, mock_err) = ("OUT_MSG", "")
        popen.returncode = mock_ret = 0


        # block on Popen creation
        def acq(a, stdout, stderr):
            sem.acquire(True)
            return mock.DEFAULT
        mock_popen.side_effect = acq


        def handler(signum, frame):
            sem.release()
        # Set the signal handler and a 5-second alarm
        signal.signal(signal.SIGALRM, handler)

        redirect = serial_redirection._SerialRedirectionThread('tty', 42, None)
        redirect.start()

        signal.alarm(1)
        redirect.stop()
        signal.alarm(0)          # Disable the alarm



    def test_process_allready_terminated_os_error(self, mock_popen):

        #
        # Does not represent the real case, where terminate would have
        # been called when the process would allready be terminated
        # but it's here for coverage
        #

        # stub Popen
        sem = Semaphore(0)
        def communicate():
            sem.acquire(True)
            return mock.DEFAULT
        def terminate():
            sem.release()
            raise OSError(3, 'No such proccess')

        popen = mock_popen.return_value
        popen.terminate.side_effect = terminate
        popen.communicate.side_effect = communicate
        popen.communicate.return_value = (mock_out, mock_err) = ("OUT_MSG", "")
        popen.returncode = mock_ret = 0

        redirect = serial_redirection._SerialRedirectionThread('tty', 42, None)
        redirect.start()
        _wait_call_count_not_null(popen.communicate, 1)
        redirect.stop()



from cStringIO import StringIO
captured_err = StringIO()
@mock.patch('sys.stderr', captured_err)
class TestParseArguments(object):
    def test_help(self):
        """
        Test normal run
        """

        for help in ('--help', '-h'):
            try:
                args = [help]
                serial_redirection.parse_arguments(args)
            except SystemExit as ret:
                assert ret.code == 0
            else:
                assert 0

    def test_valid_calls(self):
        """
        Test valid calls with nodes name
        """

        for node in config.NODES:
            args = [node]
            ret = serial_redirection.parse_arguments(args)
            assert ret == node


    def test_invalid_call(self):
        """
        Test call with invalid node name
        """
        try:
            node = 'IMPOSSIBRU'
            args = [node]
            serial_redirection.parse_arguments(args)
        except SystemExit as ret:
            assert ret.code != 0
        else:
            assert 0

