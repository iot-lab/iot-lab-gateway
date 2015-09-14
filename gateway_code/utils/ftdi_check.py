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
