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

""" gateway_code.open_nodes.node_a8_m3 unit tests files """

from mock import patch

from gateway_code.open_nodes.node_a8_m3 import NodeA8M3


@patch('gateway_code.utils.ftdi_check.ftdi_check')
def test_node_a8_m3_status(ftdi_check):
    """Test ftdi_check is correctly called."""
    node = NodeA8M3()
    ftdi_check.return_value = 42
    assert node.status() == 42
    ftdi_check.assert_called_once()
    ftdi_check.assert_called_with('a8-m3', '2232')
