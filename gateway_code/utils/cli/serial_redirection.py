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

""" CLI client for serial_redirection """

import signal
import gateway_code.board_config as board_config
from . import log_to_stderr


def _get_node(board_cfg):
    if board_cfg.linux_on_class is not None:
        # Linux open node
        return board_cfg.linux_on_class()
    return board_cfg.board_class()


def _handle_signal(signum, frame):
    # pylint:disable=unused-argument
    raise KeyboardInterrupt()


@log_to_stderr
def main():
    """ serial_redirection cli main function """
    # Catch SIGTERM signal sending by start-stop-daemon
    # init script
    signal.signal(signal.SIGTERM, _handle_signal)
    board_cfg = board_config.BoardConfig()
    node = _get_node(board_cfg)
    try:
        node.serial_redirection.start()
        print('Press Ctrl+C to stop')
        signal.pause()
    except KeyboardInterrupt:
        pass
    finally:
        node.serial_redirection.stop()
        print('Stopped')
