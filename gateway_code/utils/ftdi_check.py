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

""" Ftdi device presence check. """

import re
import subprocess
import logging
LOGGER = logging.getLogger('gateway_code')

DEV_LIST = {
    'number': r"Found (?P<dev_number>\d+) device\(s\)",
    'id': r"Device (?P<id>\d+):",
    'manufacturer': r"Manufacturer: (?P<manufacturer>.*)}",
    'description': r"Description: (?P<description>.*)",
    'serial': r"Serial: (?P<serial>.*)"
}


def ftdi_check(node, ftdi_type, description=None):
    """ Detect if a node ftdi is present 0 on success """
    LOGGER.info("Check %r node ftdi", node)

    output = subprocess.check_output(['ftdi-devices-list', '-t', ftdi_type])
    lines = (output.decode('latin-1').splitlines())
    dev_number = ftdi_parse_device_number(lines[2])
    found = (dev_number > 0) and \
            ((description is None) or
             ftdi_lookup_description(lines[3:], description))
    msg = f"{'' if found else 'No '}{node} node ftdi found"
    LOGGER.info(msg)
    return 0 if found else 1


def ftdi_parse_device_number(line):
    """ Parses device number

    >>> ftdi_parse_device_number('Found 0 device(s) \\n')
    0
    >>> ftdi_parse_device_number('Found 1 device(s) \\n')
    1
    >>> ftdi_parse_device_number('Found 2 device(s) \\n')
    2
    """
    match = re.match(DEV_LIST['number'], line.strip())
    return 0 if match is None else int(match.group(1))


def ftdi_parse_device_description(line):
    """ Parses device description

    >>> ftdi_parse_device_description('\tDescription: M3 \\n')
    'M3'
    >>> ftdi_parse_device_description('\tDescription: ControlNode \\n')
    'ControlNode'
    """
    match = re.match(DEV_LIST['description'], line.strip())
    return None if match is None else match.group(1)


def ftdi_lookup_description(lines, description):
    """ Lookup for the device description field inside the array of lines """
    assert len(lines) >= 4
    found = False
    for i in range(0, len(lines) - 1, 4):
        found = (description == ftdi_parse_device_description(lines[i + 2]))
        if found:
            break
    return found
