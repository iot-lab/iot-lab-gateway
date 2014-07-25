# -*- coding:utf-8 -*-

# pylint: disable=missing-docstring
# pylint: disable=too-many-public-methods

import unittest
import logging
from gateway_code import gateway_logging, config
import os


class TestGatewayLogging(unittest.TestCase):

    def test_multiple_calls(self):
        logger = logging.getLogger('gateway_code')

        gateway_logging.init_logger('.')
        handlers_one = logger.handlers
        gateway_logging.init_logger('.')
        handlers_two = logger.handlers

        self.assertEquals(handlers_one, handlers_two)

    def test_user_logger(self):

        logger = logging.getLogger(__name__)

        log_file = 'test_log_file.log'
        log_handler = gateway_logging.user_logger(log_file)
        logger.addHandler(log_handler)

        for i in range(0, 100):
            logger.info('Test log %d', i)

        log_handler.close()

        # file has correct permission and has data
        self.assertEquals(os.stat(log_file).st_mode & 0777, config.STAT_0666)
        self.assertNotEquals(0, os.stat(log_file).st_size)

        os.remove(log_file)
