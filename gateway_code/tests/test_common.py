# -*- coding:utf-8 -*-

import unittest
import time
from threading import Thread, RLock

from gateway_code import common


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


class TestSyncronousDecorator(unittest.TestCase):

    def test_syncronous_decorator(self):

        # using RLock as it's what I want to use at the end
        class PutAfterTime(object):
            def __init__(self):
                self.rlock = RLock()

            @common.syncronous('rlock')
            def put_after_time(self, delay, item_list, item):
                time.sleep(delay)
                item_list.append(item)

        item_list = []
        class_put = PutAfterTime()

        thr_a = Thread(target=class_put.put_after_time,
                       args=(2, item_list, 'a'))
        thr_b = Thread(target=class_put.put_after_time,
                       args=(0, item_list, 'b'))

        thr_a.start()
        time.sleep(0.5)
        thr_b.start()
        time.sleep(0.5)
        class_put.put_after_time(0, item_list, 'c')

        self.assertEquals(['a', 'b', 'c'], item_list)
