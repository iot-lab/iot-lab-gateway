#! /usr/bin/env python
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

""" CLI client for serial_redirection

Usage: serial_redirection <tty> <baudrate>

"""

import argparse
import signal
from .. import serial_redirection
from . import log_to_stderr

PARSER = argparse.ArgumentParser()
PARSER.add_argument('tty', type=str, help="Serial device")
PARSER.add_argument('baudrate', type=int, help="Serial baudrate")


@log_to_stderr
def main():
    """ serial_redirection cli main function """

    opts = PARSER.parse_args()
    redirect = serial_redirection.SerialRedirection(opts.tty, opts.baudrate)
    try:
        redirect.start()
        print 'Press Ctrl+C to stop'
        signal.pause()
    except KeyboardInterrupt:
        pass
    finally:
        redirect.stop()
        print 'Stopped'
