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


# pylint: disable=missing-docstring
# pylint <= 1.3
# pylint: disable=too-many-public-methods
# pylint >= 1.4
# pylint: disable=too-few-public-methods
# pylint: disable=no-member

import unittest
import time
from threading import Thread, RLock
import mock

from gateway_code import common


class TestLogger(unittest.TestCase):

    @mock.patch('gateway_code.common.LOGGER')
    def test_ret_logger_with_ret(self, m_logger):

        @common.logger_call("test value", 'info', 'error')
        def simple_ret(value):
            return value

        simple_ret(0)
        self.assertEqual(1, m_logger.info.call_count)
        self.assertEqual(0, m_logger.error.call_count)

        simple_ret(1)
        self.assertEqual(2, m_logger.info.call_count)
        self.assertEqual(1, m_logger.error.call_count)


class TestWaitCond(unittest.TestCase):

    def test_wait_cond_no_timeout(self):
        """ Test wait_cond """

        self.assertTrue(common.wait_cond(0, True, lambda: True))
        self.assertFalse(common.wait_cond(0, True, lambda: False))

    def test_wait_cond_with_timeout(self):
        """ Test wait_cond using a timeout value """

        t_ref = time.time()
        self.assertTrue(common.wait_cond(10., True, lambda: True))
        self.assertGreater(10, time.time() - t_ref)

        t_ref = time.time()
        self.assertFalse(common.wait_cond(0.5, True, lambda: False))
        self.assertLessEqual(0.5, time.time() - t_ref)

    def test_wait_cond_with_fct_param(self):
        """ Test wait_cond using a function with params """

        self.assertTrue(common.wait_cond(0, True, lambda x: x, True))
        self.assertTrue(common.wait_cond(0, True, lambda x: x, x=True))


class TestWaitTTY(unittest.TestCase):

    def test_wait_tty(self):
        """ Test running wait_tty fct """
        logger = mock.Mock()
        self.assertEqual(0, common.wait_tty('/dev/null', logger, 0))
        self.assertEqual(0, logger.error.call_count)
        self.assertEqual(1, common.wait_tty('no_tty_file', logger, 0))
        self.assertEqual(1, logger.error.call_count)

    def test_wait_no_tty(self):
        """ Test running wait_no_tty fct """
        self.assertEqual(0, common.wait_no_tty('no_tty_file', 0))
        self.assertEqual(1, common.wait_no_tty('/dev/null', 0))


class TestSynchronousDecorator(unittest.TestCase):

    def test_synchronous_decorator(self):

        # using RLock as it's what I want to use at the end
        class PutAfterTime:  # pylint: disable=too-few-public-methods

            def __init__(self):
                self.rlock = RLock()
                self.item_list = []

            @common.synchronous('rlock')
            def put_after_time(self, item, delay=0):
                time.sleep(delay)
                self.item_list.append(item)

        class_put = PutAfterTime()

        thr_a = Thread(target=class_put.put_after_time, args=('a', 2))

        thr_a.start()
        time.sleep(0.5)
        self.assertRaises(EnvironmentError, class_put.put_after_time, 'b')
        time.sleep(2)
        class_put.put_after_time('c')

        self.assertEqual(['a', 'c'], class_put.item_list)
