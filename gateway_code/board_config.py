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


""" Board Config """

import functools

import os

from gateway_code import profile
from gateway_code import open_nodes

# Implemented as a class to be loaded dynamically and allow mocking in tests
from gateway_code.config import (control_node_class,
                                 DEFAULT_PROFILE, read_config)


class BoardConfig(object):  # pylint:disable=too-few-public-methods
    """ Class BoardConfig, aggregates all the configuration.

    It's a class because it should be evaluated at runtime to allow mocking.
    """

    def __init__(self, board_type, hostname, cn_type='iotlab', robot=None):
        self.board_class = open_nodes.node_class(board_type)
        self.cn_class = control_node_class(cn_type)

        self.robot_type = robot
        self.node_id = hostname

        self.profile_from_dict = functools.partial(profile.Profile.from_dict,
                                                   self.board_class)
        self.default_profile = self.profile_from_dict(DEFAULT_PROFILE)

    @property
    def board_type(self):
        """Open node type."""
        return self.board_class.TYPE

    @property
    def cn_type(self):
        """Control node type."""
        return self.cn_class.TYPE

    @staticmethod
    def from_file(path):
        """ factory method, get config from a /var/local/config -like tree """
        board_type = read_config('board_type', path=path)
        control_node_type = read_config('control_node_type',
                                        'iotlab', path=path)
        robot = read_config('robot', None, path=path)
        hostname = read_config('hostname', path=path)
        return BoardConfig(board_type, hostname, control_node_type, robot)

    @staticmethod
    def from_env():
        board_type = os.environ.get('BOARD_TYPE', 'm3')
        control_node_type = os.environ.get('CONTROL_NODE_TYPE', 'no')
        robot = os.environ.get('ROBOT', None)
        hostname = os.environ.get('HOSTNAME')
        return BoardConfig(board_type, hostname, control_node_type, robot)
