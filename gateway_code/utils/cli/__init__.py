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


"""Common node utilities command line interface."""

import logging
import functools

LOGGER = logging.getLogger('gateway_code')
STREAM_STDERR = logging.StreamHandler()
STREAM_STDERR.setLevel(logging.DEBUG)


def _register_stderr_logger():
    """ADD stderr logger."""
    LOGGER.addHandler(STREAM_STDERR)


def _unregister_stderr_logger():
    """Remove stderr logger."""
    LOGGER.removeHandler(STREAM_STDERR)


def log_to_stderr(func):
    """Decorator to add a stderr streamhandler."""
    @functools.wraps(func)
    def _wrapped(*args, **kwargs):
        """Wrapped with redirected logs."""
        try:
            _register_stderr_logger()
            return func(*args, **kwargs)
        finally:
            _unregister_stderr_logger()
    return _wrapped
