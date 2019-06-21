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

""" gateway_code.control_node (No) unit tests files """

import mock

from gateway_code.control_nodes.cn_no import ControlNodeNo


def test_control_node_no_basic():
    """Test basic empty features when there's no control node."""

    # Setup always returns 0
    assert ControlNodeNo.setup() == 0

    # Flash and status does nothing
    cn_no = ControlNodeNo('test', None)
    assert cn_no.start('test') == 0
    assert cn_no.stop() == 0
    assert cn_no.flash() == 0
    assert cn_no.status() == 0
    assert cn_no.autotest_setup(None) == 0
    assert cn_no.autotest_teardown(None) == 0
    assert cn_no.start_experiment("test") == 0
    assert cn_no.stop_experiment() == 0


@mock.patch("gateway_code.control_nodes.cn_no.ControlNodeNo.configure_profile")
def test_start_stop_experiment(config):
    """Test starting and stoping experiment."""
    config.return_value = 0
    cn_no = ControlNodeNo('test', None)
    assert cn_no.start_experiment("test") == 0
    config.assert_called_with("test")
    assert cn_no.stop_experiment() == 0
    config.assert_called_with(None)
