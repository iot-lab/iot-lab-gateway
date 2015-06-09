# -*- coding:utf-8 -*-
""" Ftdi device presence check. """

import subprocess
import logging
LOGGER = logging.getLogger('gateway_code')


def ftdi_check(node, ftdi_type):
    """ Detect if a node ftdi is present 0 on success """
    LOGGER.info("Check %r node ftdi", node)

    output = subprocess.check_output(['ftdi-devices-list', '-t', ftdi_type])

    found = 'Found 1 device(s)' in output.splitlines()
    LOGGER.info(("" if found else "No ") + "%r node ftdi found" % node)
    return 0 if found else 1
