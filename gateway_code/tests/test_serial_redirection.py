# -*- coding:utf-8 -*-

""" test serial_redirection module """

import mock
import unittest

from cStringIO import StringIO
import threading

from gateway_code.serial_redirection import SerialRedirection
from gateway_code import serial_redirection

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=too-many-public-methods


@mock.patch('sys.stderr', StringIO())
class TestMainFunction(unittest.TestCase):

    def setUp(self):
        self.popen_patcher = mock.patch('subprocess.Popen')
        self.popen_class = self.popen_patcher.start()
        self.popen = self.popen_class.return_value

        self.popen.wait.side_effect = self._wait
        self.popen.wait.return_value = 0
        self.popen.terminate.side_effect = self._terminate

        self.unlock_wait = threading.Event()
        self.wait = threading.Event()

        self.redirect = None

    def tearDown(self):
        self.popen.stop()
        if self.redirect is not None:
            self.redirect.stop()  # last chance cleanup

    def _wait(self):
        self.wait.set()
        self.unlock_wait.wait()
        self.unlock_wait.clear()
        return mock.DEFAULT

    def _terminate(self):
        self.unlock_wait.set()

    def test_simple_start(self):

        redirection = SerialRedirection('m3')

        self.assertEquals(redirection.stop(), 1)  # cannot stop before start
        self.assertEquals(redirection.start(), 0)
        self.assertEquals(redirection.start(), 1)  # only one start

        self.wait.wait()

        redirection.stop()

        self.assertTrue(self.popen.wait.call_count >= 1)
        self.assertTrue(self.popen.terminate.call_count >= 1)

    def test_program_error(self):
        """ Test program error """
        # on first call 'wait' is called
        # on second call, 'self._wait' is called
        def wait():
            self.popen.wait.side_effect = self._wait
            return mock.DEFAULT

        # Popen mock
        self.popen.wait.side_effect = wait
        self.popen.wait.return_value = 42

        with mock.patch('gateway_code.serial_redirection.LOGGER.error') \
                as mock_logger:
            redirection = SerialRedirection('m3')

            self.assertEquals(redirection.start(), 0)
            self.wait.wait()
            redirection.stop()

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

        self.popen.wait.side_effect = self._wait
        self.popen.wait.return_value = 0
        self.popen.terminate.side_effect = self._terminate

        self.unlock_wait = threading.Event()
        self.wait = threading.Event()

        self.redirect = None

    def tearDown(self):
        self.popen.stop()
        if self.redirect is not None:
            self.redirect.stop()  # last chance cleanup

    def _wait(self):
        self.wait.set()
        self.unlock_wait.wait()
        self.unlock_wait.clear()
        return mock.DEFAULT

    def _terminate(self):
        self.unlock_wait.set()

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

        def blocking_popen(*args):  # pylint:disable=unused-argument
            unlock_popen.wait()  # block on Popen creation
            return mock.DEFAULT

        def wait():
            self.popen_class.side_effect = None
            return self._wait()

        self.popen_class.side_effect = blocking_popen
        self.popen.wait.side_effect = wait

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
        self.wait.wait()
        self.redirect.stop()


@mock.patch('gateway_code.serial_redirection._SerialRedirectionThread')
class TestSerialRedirectionInit(unittest.TestCase):
    """ Test the SerialRedirection class init """

    def test__init(self, _):
        """ Test init calls"""
        # valid inits
        for node in ('m3', 'gwt', 'a8'):
            SerialRedirection(node)

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
