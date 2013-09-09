# -*- coding:utf-8 -*-

import unittest
import logging
from gateway_code import gateway_logging

class TestGatewayLogging(unittest.TestCase):

    def test_multiple_calls(self):
        logger = logging.getLogger('gateway_code')

        gateway_logging.init_logger('.')
        handlers_one = logger.handlers
        gateway_logging.init_logger('.')
        handlers_two = logger.handlers

        self.assertEquals(handlers_one, handlers_two)
