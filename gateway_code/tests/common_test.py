# -*- coding:utf-8 -*-

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
        self.assertEquals(0, common.wait_tty('/dev/null', logger))
        self.assertEquals(0, logger.error.call_count)
        self.assertNotEquals(0, common.wait_tty('no_tty_file', logger))
        self.assertEquals(1, logger.error.call_count)


class TestSyncronousDecorator(unittest.TestCase):

    def test_syncronous_decorator(self):

        # using RLock as it's what I want to use at the end
        class PutAfterTime(object):  # pylint: disable=too-few-public-methods

            def __init__(self):
                self.rlock = RLock()
                self.item_list = []

            @common.syncronous('rlock')
            def put_after_time(self, delay, item):
                time.sleep(delay)
                self.item_list.append(item)

        class_put = PutAfterTime()

        thr_a = Thread(target=class_put.put_after_time, args=(2, 'a'))
        thr_b = Thread(target=class_put.put_after_time, args=(0, 'b'))

        thr_a.start()
        time.sleep(0.5)
        thr_b.start()
        time.sleep(0.5)
        class_put.put_after_time(0, 'c')

        self.assertEquals(['a', 'b', 'c'], class_put.item_list)
