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


"""Helper module for calling a command in a subprocess."""

import shlex

import logging

from . import subprocess_timeout

LOGGER = logging.getLogger('gateway_code')


def call_cmd(command_str, out=None, timeout=30):
    """Call a command in a subprocess."""
    kwargs = {'args': shlex.split(command_str), 'stdout': out, 'stderr': out}
    try:
        return subprocess_timeout.call(timeout=timeout, **kwargs)
    except subprocess_timeout.TimeoutExpired as exc:
        LOGGER.error("Command '%s' timeout: %s", command_str, exc)
        return 1
