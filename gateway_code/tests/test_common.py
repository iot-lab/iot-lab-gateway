# -*- coding:utf-8 -*-

import unittest
import mock
import Queue

from gateway_code import common


class TestEmptyQueue(unittest.TestCase):

    def test_empty_queue_one_element(self):

        queue = Queue.Queue(1)
        common.empty_queue(queue)
        self.assertTrue(queue.empty())

        queue.put('TEST')
        common.empty_queue(queue)
        self.assertTrue(queue.empty())

    def test_empty_queue_multiple_elemements(self):

        queue = Queue.Queue(5)
        common.empty_queue(queue)
        self.assertTrue(queue.empty())


        queue.put('1')
        queue.put('2')
        common.empty_queue(queue)
        self.assertTrue(queue.empty())


        queue.put('1')
        queue.put('2')
        queue.put('3')
        queue.put('4')
        queue.put('5')
        common.empty_queue(queue)
        self.assertTrue(queue.empty())



