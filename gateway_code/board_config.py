# -*- coding:utf-8 -*-

""" Board Config """

import os
import functools
from gateway_code import config
from gateway_code import profile


# Implemented as a class to be loaded dynamically and allow mocking in tests
class BoardConfig(object):  # pylint:disable=too-few-public-methods
    """ Class BoardConfig, aggregates all the configuration.

    It's a class because it should be evaluated at runtime to allow mocking.
    """

    def __init__(self):
        self.board_type = config.read_config('board_type')
        self.board_class = config.open_node_class(self.board_type)
        self.robot_type = config.read_config('robot', None)
        self.node_id = os.uname()[1]

        self.profile_from_dict = functools.partial(profile.Profile.from_dict,
                                                   self.board_class)
        self.default_profile = self.profile_from_dict(config.DEFAULT_PROFILE)
