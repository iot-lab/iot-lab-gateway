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
import json
from nose.plugins.attrib import attr

from mock import patch

import gateway_code.rest_server
import gateway_code.board_config


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) + '/'


# pylint: disable=too-many-public-methods
@attr('integration')
class GatewayCodeMock(unittest.TestCase):
    """ gateway_code mock for integration tests  """

    @classmethod
    def setUpClass(cls):

        if os.uname()[4] != 'armv7l':
            raise unittest.SkipTest("Skip board embedded tests")

        g_m = gateway_code.rest_server.GatewayManager('.')
        g_m.setup()
        cls.app = gateway_code.rest_server.GatewayRest(g_m)

    @classmethod
    def tearDownClass(cls):
        patch.stopall()

    def setUp(self):
        # get quick access to class attributes
        self.app = type(self).app
        self.g_m = self.app.gateway_manager

        self.board_cfg = gateway_code.board_config.BoardConfig()

        self.cn_measures = []
        self.g_m.control_node.cn_serial.measures_debug = self.cn_measure

        self.request_patcher = patch('gateway_code.rest_server.request')
        self.request = self.request_patcher.start()
        self.request.query = mock.Mock(timeout='0')  # no timeout by default

        with open(CURRENT_DIR + 'profile.json') as prof:
            self.profile_dict = json.load(prof)

    def cn_measure(self, measure):
        """ Store control node measures """
        self.cn_measures.append(measure.split(' '))

    def tearDown(self):
        self.request_patcher.stop()
        self.app.exp_stop()  # just in case, post error cleanup
