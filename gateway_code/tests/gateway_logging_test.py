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
# pylint: disable=too-many-public-methods

import unittest
import logging
from gateway_code import gateway_logging
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

        # file has data
        self.assertNotEquals(0, os.path.getsize(log_file))

        os.remove(log_file)
