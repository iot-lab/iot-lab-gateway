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

import threading
import functools


class PeriodicTimer(object):
    """Python periodic Timer with instant cancellation."""

    def __init__(self, interval, function, args=[], kwargs={}):
        self.function = function
        self.create_timer = functools.partial(
            threading.Timer,
            interval, self.timer_callback, args, kwargs)

        # Shared objects, should be used under lock
        self._lock = threading.Lock()
        self._active = False
        self._timer = None

    def start(self):
        """Start periodic timer.

        Unlike threading.Timer it can be reused.
        If timer is active, reset period.
        """

        self.cancel()

        with self._lock:
            self._start()

    def _start(self):
        """Start timer, should be used under lock."""
        self._active = True
        self._timer = self.create_timer()
        self._timer.start()

    def cancel(self):
        """Cancel current timer."""
        with self._lock:
            self._active = False
            self._cancel()
            self._timer = None

    def _cancel(self):
        """Safe cancel that catches exceptions."""
        try:
            self._timer.cancel()
        except AttributeError:
            pass

    def timer_callback(self, *args, **kwargs):
        """Function run when timer expires."""
        with self._lock:
            self._timer = None
            if not self._active:
                return

        self.function(*args, **kwargs)

        # Start new timer if still active
        with self._lock:
            if self._active:
                self._start()
