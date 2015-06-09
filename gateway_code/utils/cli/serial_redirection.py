#! /usr/bin/env python
# -*- coding:utf-8 -*-
""" CLI client for serial_redirection

Usage: serial_redirection <tty> <baudrate>

"""

import argparse
import signal
from .. import serial_redirection

PARSER = argparse.ArgumentParser()
PARSER.add_argument('tty', type=str, help="Serial device")
PARSER.add_argument('baudrate', type=int, help="Serial baudrate")


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
