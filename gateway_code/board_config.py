#! /usr/bin/env python
# -*- coding:utf-8 -*-

# pylint: disable=no-self-use

""" Board Config """

import os
from importlib import import_module
from gateway_code import config


class BoardConfig(object):
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

        self.board_type = self._find_board_type()
        self.hostname = self.get_hostname()

        try:
            open_node_path = config.OPEN_NODES_PATH.format(self.board_type)
            module = import_module(open_node_path)
            self.board_class = getattr(
                module, 'Node' + self.board_type.title())
        except ImportError:
            raise ValueError(
                'The class %r is not implemented' % open_node_path)

    def clear_instance(self):
        """ Reset the instance contained in the Singleton """
        self._instance = None
        self._is_init = False

    @staticmethod
    def get_hostname():
        """ Return the board hostname """
        return os.uname()[1]

    def robot_type(self):
        """ Return robot type None, 'roomba' """
        return self._get_conf('robot', config.GATEWAY_CONFIG_PATH)

    def _get_conf(self, key, path, raise_error=False):
        """
        Load config from file given as key

        :param key: config file name
        :param raise_error: select if exceptions are silenced or raised
        """
        # load from file
        try:
            _file = open(os.path.join(path, key))
            readed = _file.read().strip().lower()
            _file.close()
        except IOError as err:
            readed = None
            if raise_error:
                raise err
        return readed

    def _find_board_type(self):
        """ Return the board type """
        return self._get_conf('board_type', config.GATEWAY_CONFIG_PATH,
                              raise_error=True)
