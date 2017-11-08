# -*- coding: utf-8 -*-

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

""" Implementation of common mocks for integration tests """

import os
import unittest
import mock
import webtest
from nose.plugins.attrib import attr

import gateway_code.rest_server
import gateway_code.board_config


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) + '/'


def run_integration():
    """Tell if integration tests should be run."""
    if 'IOTLAB_GATEWAY_NO_INTEGRATION_TESTS' in os.environ:
        return False
    # iotlab-gateways
    if os.uname()[4] == 'armv7l':
        return True
    # manual tests without control node
    if 'IOTLAB_GATEWAY_CFG_DIR' in os.environ:
        return True
    return False


# pylint: disable=too-many-public-methods
@attr('integration')
class GatewayCodeMock(unittest.TestCase):
    """ gateway_code mock for integration tests  """

    @classmethod
    def setUpClass(cls):

        if not run_integration():
            raise unittest.SkipTest("Skip board embedded tests")

        cls.gateway_manager = gateway_code.rest_server.GatewayManager('.')
        cls.gateway_manager.setup()

        app = gateway_code.rest_server.GatewayRest(cls.gateway_manager)
        cls.server = webtest.TestApp(app)

    @classmethod
    def tearDownClass(cls):
        mock.patch.stopall()

    def setUp(self):
        # get quick access to class attributes
        self.server = type(self).server
        self.g_m = type(self).gateway_manager

        self.board_cfg = gateway_code.board_config.BoardConfig()

        self.cn_measures = []
        if hasattr(self.g_m.control_node, 'cn_serial'):
            self.g_m.control_node.cn_serial.measures_debug = self.cn_measure

    def cn_measure(self, measure):
        """ Store control node measures """
        self.cn_measures.append(measure.split(' '))

    def tearDown(self):
        mock.patch.stopall()
        # Post error cleanup
        self.server.delete('/exp/stop')
