#! /usr/bin/env python
# -*- coding:utf-8 -*-

import mock
import unittest

from cStringIO import StringIO
import threading

from gateway_code.serial_redirection import SerialRedirection
from gateway_code import serial_redirection

_SerialRedirection_str = ('gateway_code.serial_redirection.' +
                          '_SerialRedirectionThread')


@mock.patch('sys.stderr', StringIO())
class TestMainFunction(unittest.TestCase):

    def setUp(self):
        self.popen_patcher = mock.patch('subprocess.Popen')
        self.popen_class = self.popen_patcher.start()
        self.popen = self.popen_class.return_value

        self.popen.communicate.side_effect = self._communicate
        self.popen.communicate.return_value = ("OUT", "ERR")
        self.popen.terminate.side_effect = self._terminate
        self.popen.returncode = 0

        self.unlock_communicate = threading.Event()
        self.communicate_called = threading.Event()

        self.redirect = None

    def tearDown(self):
        self.popen.stop()
        if self.redirect is not None:
            self.redirect.stop()  # last chance cleanup

    def _communicate(self):
        self.communicate_called.set()
        self.unlock_communicate.wait()
        self.unlock_communicate.clear()
        return mock.DEFAULT

    def _terminate(self):
        self.unlock_communicate.set()

    def test_simple_start(self):

        redirection = SerialRedirection('m3')

        self.assertEquals(redirection.stop(),  1)  # cannot stop before start
        self.assertEquals(redirection.start(), 0)
        self.assertEquals(redirection.start(), 1)  # only one start

        self.communicate_called.wait()

        redirection.stop()

        self.assertTrue(self.popen.communicate.call_count >= 1)
        self.assertTrue(self.popen.terminate.call_count >= 1)

    def test_program_error(self):
        """
        Test program error
        """
        def communicate():
            self.popen.communicate.side_effect = self._communicate
            return mock.DEFAULT
        # Popen mock
        self.popen.communicate.side_effect = communicate
        self.popen.returncode = 42

        with mock.patch('gateway_code.serial_redirection.LOGGER.error') \
                as mock_logger:
            self.redirection = SerialRedirection('m3')

            self.assertEquals(self.redirection.start(), 0)
            self.communicate_called.wait()
            self.redirection.stop()

            mock_logger.assert_called_with(
                'Open node serial redirection exit: %d', 42)

    def test_simple_case(self):
        def wait_mock():
            """ 'wait' will call the ctrl+c handler has if a ctrl+c was got """
            import signal
            handler = signal.getsignal(signal.SIGINT)  # get ctrl+c handler
            handler(None, None)

        with mock.patch('gateway_code.serial_redirection.Event') as mock_event:
            event = mock_event.return_value
            event.wait.side_effect = wait_mock

            serial_redirection._main(['serial_redirection.py', 'm3'])
            self.assertEquals(event.wait.call_count, 1)

    @mock.patch('gateway_code.serial_redirection.SerialRedirection')
    def test_error_with_start_redirection(self, mock_serial_class):
        # start SerialRedirection fail
        (mock_serial_class.return_value).start.return_value = 1
        self.assertRaises(SystemExit,
                          serial_redirection._main,
                          ['serial_redirection.py', 'm3'])


class TestSerialRedirectionAndThread(unittest.TestCase):

    def setUp(self):
        self.popen_patcher = mock.patch('subprocess.Popen')
        self.popen_class = self.popen_patcher.start()
        self.popen = self.popen_class.return_value

        self.popen.communicate.side_effect = self._communicate
        self.popen.communicate.return_value = ("OUT", "ERR")
        self.popen.terminate.side_effect = self._terminate
        self.popen.returncode = 0

        self.unlock_communicate = threading.Event()
        self.communicate_called = threading.Event()

        self.redirect = None

    def tearDown(self):
        self.popen.stop()
        if self.redirect is not None:
            self.redirect.stop()  # last chance cleanup

    def _communicate(self):
        self.communicate_called.set()
        self.unlock_communicate.wait()
        self.unlock_communicate.clear()
        return mock.DEFAULT

    def _terminate(self):
        self.unlock_communicate.set()

    def test_terminate_on_non_started_process(self):
        """
        Test terminate with self.redirector_process is None
        """

        # Start thread
        # blocks on Popen
        # run stop
        # sigalarm unlocks popen so that terminate will work on next call

        import signal

        unlock_popen = threading.Event()

        def blocking_popen(a, stdout, stderr):
            unlock_popen.wait()  # block on Popen creation
            return mock.DEFAULT

        def communicate():
            self.popen_class.side_effect = None
            return self._communicate()

        self.popen_class.side_effect = blocking_popen
        self.popen.communicate.side_effect = communicate

        self.redirect = serial_redirection._SerialRedirectionThread('tty', 42)
        self.redirect.start()

        signal.signal(signal.SIGALRM, (lambda a, b: unlock_popen.set()))
        signal.alarm(1)  # alarm will release popen
        self.redirect.stop()
        signal.alarm(0)          # Disable the alarm

    def test_process_allready_terminated_os_error(self):
        #
        # Does not represent the real case, where terminate would have
        # been called when the process would allready be terminated
        # but it's here for coverage
        #

        def terminate():
            self.popen.terminate.side_effect = self._terminate
            self._terminate()
            raise OSError(3, 'No such proccess')

        self.popen.terminate.side_effect = terminate

        self.redirect = serial_redirection._SerialRedirectionThread('tty', 42)
        self.redirect.start()
        self.communicate_called.wait()
        self.redirect.stop()


@mock.patch(_SerialRedirection_str)
class TestSerialRedirectionInit(unittest.TestCase):
    """ Test the SerialRedirection class init """

    def test_valid_init(self, mock_thread):
        """ Test valid init calls"""
        for node in ('m3', 'gwt', 'a8'):
            redirection = SerialRedirection(node)

    def test_invalid_init(self, mock_thread):
        """ Test Invalid init calls """
        # invalid node name
        self.assertRaises(ValueError, SerialRedirection, 'INVALID_NODE')


@mock.patch('sys.stderr', StringIO())
class TestParseArguments(unittest.TestCase):
    def test_command_line_calls(self):
        from gateway_code import config
        # valid
        for node in config.NODES:
            self.assertEquals(serial_redirection._parse_arguments([node]),
                              node)
        # invalid calls
        args = ['INEXISTANT_NODE']
        self.assertRaises(SystemExit,
                          serial_redirection._parse_arguments, args)
