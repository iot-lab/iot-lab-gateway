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
""" control nodes plugins tests """
from __future__ import print_function

from mock import patch

from gateway_code.nodes import all_control_nodes_types, control_node_class


@patch('gateway_code.utils.mjpg_streamer.MJPG_STREAMER_LOG_FILE',
       '/tmp/mjpg_streamer_test.log')
def test_nodes_classes():
    """Test loading all implemented control nodes implementation."""
    for node in all_control_nodes_types():
        # No exception
        print(node)
        node_class = control_node_class(node)
        node_class(None, None)
        print(node_class)
