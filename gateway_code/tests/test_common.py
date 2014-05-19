# -*- coding:utf-8 -*-

import unittest
import time

from gateway_code import common


class TestWaitCond(unittest.TestCase):

    def test_wait_cond_no_timeout(self):
        """ Test wait_cond """

        self.assertEquals(0, common.wait_cond(0, True, lambda: True))
        self.assertEquals(1, common.wait_cond(0, True, lambda: False))


    def test_wait_cond_with_timeout(self):

        t_ref = time.time()
        self.assertEquals(0, common.wait_cond(10., True, lambda: True))
        self.assertGreater(10, time.time() - t_ref)

        t_ref = time.time()
        self.assertEquals(1, common.wait_cond(0.5, True, lambda: False))
        self.assertLessEqual(0.5, time.time() - t_ref)

