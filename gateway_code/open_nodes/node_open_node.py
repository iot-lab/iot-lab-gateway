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
""" contains an implementation of The Zolertia Firefly open node"""

import logging
from glob import glob

from gateway_code.autotest.autotest import FatalError
from gateway_code.open_nodes import all_nodes_types, node_class


LOGGER = logging.getLogger('gateway_code')


def actual_board():
    boards = {
        board_type: node_class(board_type) for board_type in all_nodes_types()
    }
    tty_files = glob('/dev/iotlab/*')
    if len(tty_files) != 1:
        LOGGER.error('Cant decide what board to use, it seems '
                     'like multiple boards are plugged')
        LOGGER.error('TTY files : [' + ','.join(tty_files)+']')
        raise FatalError('open_node can\'t decide a board to use')
    tty_file = tty_files[0]
    for board, board_class in boards.items():
        if board_class.TTY == tty_file:
            return board_class
    error_msg = 'TTY %s not recognized as an implemented board TTY'
    raise FatalError(error_msg % tty_file)


class NodeOpenNode(object):
    """
    Open node that actually decides at runtime what its config is
    This class reads the file, if present, in /dev/iotlab/tty* to decide
    """

    TYPE = 'open_node'

    def __new__(cls, *args, **kwargs):
        # Hijack the __new__, return an instance of the detected board's class
        board = actual_board()
        return board.__new__(board, *args, **kwargs)

    # stubs, just to survice the node_class('open_node') call
    AUTOTEST_AVAILABLE = ['echo', 'get_time']
    ELF_TARGET = ('ELFCLASS32', 'EM_ARM')
    TTY = 'no board detected yet'