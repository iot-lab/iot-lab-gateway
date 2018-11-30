# -*- coding:utf-8 -*-

# This file is a part of IoT-LAB gateway_code
# Copyright (C) 2015 INRIA (Contact: admin@iot-lab.info)
# Contributor(s) : see AUTHORS file
#
# This software is governed by the CeCILL license under French law
# and abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# http://www.cecill.info.
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.

""" tests for utils/tools FlashTool """
# pylint: disable=redefined-outer-name

import time
import unittest

import pytest
from mock import mock

from gateway_code.utils import subprocess_timeout
from gateway_code.utils.tools import FlashTool


class TestsCall(unittest.TestCase):
    """ Tests FlashTool call timeout """
    def setUp(self):
        self.timeout = 5
        self.tool = FlashTool(timeout=self.timeout)
        self.tool.args = mock.Mock()

    def test_timeout_call(self):
        """Test timeout reached."""
        self.tool.args.return_value = {'args': ['sleep', '10']}
        t_0 = time.time()
        ret = self.tool.call_cmd('sleep')
        t_end = time.time()

        # Not to much more
        self.assertLess(t_end - t_0, self.timeout + 1)
        self.assertNotEqual(ret, 0)

    def test_no_timeout(self):
        """Test timeout not reached."""
        self.tool.args.return_value = {'args': ['sleep', '1']}
        t_0 = time.time()
        ret = self.tool.call_cmd('sleep')
        t_end = time.time()

        # Strictly lower here
        self.assertLess(t_end - t_0, self.timeout - 1)
        self.assertEqual(ret, 0)


@pytest.fixture()
def logger_mock():
    """mocking LOGGER"""
    with mock.patch('gateway_code.utils.tools.LOGGER') as mocked:
        yield mocked


@pytest.fixture()
def call_mock():
    """mocking subprocess_timeout.call"""
    with mock.patch('gateway_code.utils.subprocess_timeout.call') as mocked:
        yield mocked


# verb True/False
# returncode 0/1
# timeout/notimeout
@pytest.mark.parametrize(['verb', 'returncode', 'timeout'], [
    ('verbose', 'call success', 'timeout'),
    ('verbose', 'call success', '!timeout'),
    ('verbose', 'call fail', ' timeout'),
    ('verbose', 'call fail', '!timeout'),
    ('!verbose', 'call success', 'timeout'),
    ('!verbose', 'call success', '!timeout'),
    ('!verbose', 'call fail', 'timeout'),
    ('!verbose', 'call fail', '!timeout'),
])
def test_stdout_verb(call_mock, logger_mock, verb, returncode, timeout):
    """ Tests FlashTool output """
    test_output = '**test_output**'
    verb = verb == 'verbose'
    returncode = 0 if returncode == 'success' else 1
    timeout = timeout == 'timeout'

    def mocked_call(*popenargs, **kwargs):  # pylint: disable= unused-argument
        """mocking stdout write, timeout and returncode"""
        stdout = kwargs['stdout']
        stdout.write(test_output)
        if timeout:
            raise subprocess_timeout.TimeoutExpired('', 1)
        return returncode

    call_mock.side_effect = mocked_call

    tool = FlashTool(verb=verb)
    tool.call_cmd('unused command')

    if verb and not timeout:
        # we should see the output in the LOGGER.info
        output_info = str(logger_mock.info.call_args)
        assert test_output in output_info

    if timeout or returncode != 0:
        # we should see the output in the LOGGER.error
        output_error = str(logger_mock.error.call_args)
        assert test_output in output_error
