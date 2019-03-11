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

""" gateway_code.open_nodes.node_lora_gateway unit tests files """

import subprocess
from mock import patch

from gateway_code.open_nodes.node_lora_gateway import NodeLoraGateway

# pylint:disable=unused-argument


@patch('subprocess.Popen')
@patch('subprocess.check_output')
@patch('gateway_code.utils.external_process.ExternalProcess.start')
def test_setup(start, check_output, popen):
    """Test lora_gateway node setup."""
    check_output.return_value = 42
    start.return_value = 0
    node = NodeLoraGateway()

    assert node.setup() == 0
    assert check_output.call_count == 1
    assert start.call_count == 2

    start.call_count = 0
    check_output.call_count = 0

    start.return_value = 1
    assert node.setup() == 2
    assert check_output.call_count == 0
    assert start.call_count == 2


@patch('gateway_code.open_nodes.node_lora_gateway.'
       'LORA_PKT_FORWARDER_MAX_TRIES', 1)
@patch('time.sleep')
@patch('subprocess.Popen')
@patch('subprocess.check_output')
def test_setup_no_pkt_forwarder(check, popen, sleep):
    """Smoke test when no pkt forwarder is running."""
    check.side_effect = subprocess.CalledProcessError("test", "test")
    NodeLoraGateway()


@patch('subprocess.Popen')
@patch('subprocess.check_output')
@patch('gateway_code.utils.external_process.ExternalProcess.stop')
def test_teardown(stop, check_output, popen):
    """Test lora_gateway node teardown."""
    check_output.return_value = 42
    stop.return_value = 0

    node = NodeLoraGateway()
    assert node.teardown() == 0
    assert check_output.call_count == 1
    assert stop.call_count == 2

    check_output.call_count = 0
    stop.call_count = 0

    stop.return_value = 1
    assert node.teardown() == 2
    assert check_output.call_count == 0
    assert stop.call_count == 2
