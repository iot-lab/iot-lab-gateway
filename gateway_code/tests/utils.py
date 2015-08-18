# -*- coding: utf-8 -*-
""" Utilities for tests """

import mock
import os


def read_config_mock(board_type, **kwargs):
    """ Mock for gateway_config.config.read_config with
    board_type and other keys """

    config_dict = kwargs.copy()
    config_dict['board_type'] = board_type

    def read_config(key, default=IOError):
        """ read_config_mock """
        try:
            return config_dict[key]
        except KeyError:
            if default is IOError:
                raise IOError()
            return default

    return mock.Mock(side_effect=read_config)


# Help mocking config.GATEWAY_CONFIG_PATH
CFG_VAR_PATH = 'gateway_code.config.GATEWAY_CONFIG_PATH'


def test_cfg_dir(name):
    """ Return config directory in tests/ """
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(cur_dir, 'config', name)
