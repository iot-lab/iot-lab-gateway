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

""" Utilities for tests """

import os
import mock

# Help mocking config.read_config
from gateway_code.board_config import BoardConfig

READ_CONFIG = 'gateway_code.config.read_config'


def read_config_mock(board_type, **kwargs):
    """ Mock for gateway_config.config.read_config with
    board_type and other keys """

    config_dict = kwargs.copy()
    config_dict['board_type'] = board_type
    config_dict.setdefault('hostname', '%s-00' % board_type)

    def read_config(key, default=IOError):
        """ read_config_mock """
        try:
            return config_dict[key]
        except KeyError:
            if default is IOError:
                raise IOError()
            return default

    return mock.Mock(side_effect=read_config)


def get_config_mock(board_type):
    """BoardConfig Mock
    board_type and other keys """
    return BoardConfig(board_type, hostname='%s-00' % board_type)


# Help mocking config.GATEWAY_CONFIG_PATH
CFG_VAR_PATH = 'gateway_code.config.GATEWAY_CONFIG_PATH'


def test_cfg_dir(name):
    """ Return config directory in tests/ """
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cur_dir, 'config', name)
