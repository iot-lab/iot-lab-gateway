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

""" gateway_code.open_nodes.node_rtl_sdr unit tests files """

import shlex
from mock import patch

from gateway_code.open_nodes.node_rtl_sdr import NodeRtlSdr, YKUSHCMD


@patch('subprocess.call')
@patch('gateway_code.utils.external_process.ExternalProcess.start')
def test_setup(rtl_tcp_start, call):
    """Test rtl_sdr node setup."""
    call.return_value = 0
    rtl_tcp_start.return_value = 0
    ykushcmd = YKUSHCMD.format(model="", cmd="-u", port="3")
    node = NodeRtlSdr()

    assert node.setup() == 0
    assert call.call_count == 1
    assert rtl_tcp_start.call_count == 1
    call.assert_called_with(shlex.split(ykushcmd))

    call.call_count = 0
    rtl_tcp_start.call_count = 0

    call.return_value = 1
    assert node.setup() == 1
    assert call.call_count == 1
    assert rtl_tcp_start.call_count == 1
    call.assert_called_with(shlex.split(ykushcmd))


@patch('subprocess.call')
@patch('gateway_code.utils.external_process.ExternalProcess.stop')
def test_teardown(rtl_tcp_stop, call):
    """Test rtl_sdr node teardown."""
    call.return_value = 0
    rtl_tcp_stop.return_value = 0
    ykushcmd = YKUSHCMD.format(model="", cmd="-d", port="3")

    node = NodeRtlSdr()
    assert node.teardown() == 0
    assert call.call_count == 1
    assert rtl_tcp_stop.call_count == 1
    call.assert_called_with(shlex.split(ykushcmd))

    call.call_count = 0
    rtl_tcp_stop.call_count = 0

    call.return_value = 1
    assert node.teardown() == 1
    assert call.call_count == 1
    assert rtl_tcp_stop.call_count == 1
    call.assert_called_with(shlex.split(ykushcmd))
