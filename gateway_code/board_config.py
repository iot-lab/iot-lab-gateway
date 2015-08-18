# -*- coding:utf-8 -*-

""" Board Config """

import os
from gateway_code import config


# Implemented as a class to be loaded dynamically and allow mocking in tests
class BoardConfig(object):  # pylint:disable=too-few-public-methods
    """
    Class BoardConfig, used to get all the informations on the actual
    node this class is implemented as a Singleton
    """
    # The unique instance of the class Board Config
    _instance = None

    # We define a new contructor to respect the Singleton patern
    def __new__(cls):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
            cls._is_init = False
        return cls._instance

    # The initialisation of the class
    def __init__(self):
        if self._is_init:
            return
        self._is_init = True

        self.board_type = config.read_config('board_type')
        self.board_class = config.open_node_class(self.board_type)
        self.robot_type = config.read_config('robot', None)
        self.hostname = os.uname()[1]

    @classmethod
    def clear_instance(cls):
        """ Reset the instance contained in the Singleton """
        cls._instance = None
        cls._is_init = False
