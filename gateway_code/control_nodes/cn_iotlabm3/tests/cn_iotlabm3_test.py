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

""" gateway_code.control_node (iotlabm3) unit tests files """

from mock import Mock, patch

from gateway_code.control_nodes.cn_iotlabm3 import ControlNodeIotlabm3


def test_cn_iotlabm3_status():
    """Test status method of iotlabm3 control node."""
    # Flash and status does nothing
    with patch('gateway_code.utils.ftdi_check.ftdi_check') as ftdi_check:
        node = ControlNodeIotlabm3('test', None)
        ftdi_check.return_value = 42
        assert node.status() == 42
        ftdi_check.assert_called_with('controlNode', '2232')


def test_cn_iotlabm3_start_stop():
    """Test open_start/open_stop methods of iotlabm3 control node."""
    cn_iotlabm3 = ControlNodeIotlabm3('test', None)
    assert cn_iotlabm3.open_start() == 0
    assert cn_iotlabm3.open_stop() == 0


@patch('gateway_code.control_nodes.cn_iotlab.cn_protocol.Protocol.send_cmd')
def test_configure_profile(send_cmd):
    """Test configure_profile method of iotlabm3 control node."""
    send_cmd.return_value = 0
    cn_iotlabm3 = ControlNodeIotlabm3('test', None)
    profile = Mock()
    profile.radio = None
    assert cn_iotlabm3.configure_profile(profile) == 0
    send_cmd.assert_called_with(['config_radio_stop'])

    profile.radio = Mock()
    profile.radio.mode = 'rssi'
    profile.radio.channels = ['1', '3', '2']
    profile.radio.period = 10
    profile.radio.num_per_channel = 42
    assert cn_iotlabm3.configure_profile(profile) == 0
    send_cmd.assert_called_with(['config_radio_measure',
                                 '1,2,3', '10', '42'])

    profile.radio.mode = 'sniffer'
    assert cn_iotlabm3.configure_profile(profile) == 0
    send_cmd.assert_called_with(['config_radio_sniffer', '1,2,3', '10'])
