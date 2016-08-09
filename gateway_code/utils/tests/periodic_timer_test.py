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


""" test periodic_timer module """

import time
import unittest

import mock

from ..periodic_timer import PeriodicTimer


class TestPeriodicTimer(unittest.TestCase):

    def test_timer(self):
        """Test periodic timer."""
        period = 0.01
        args = (1, 2, 3)
        kwargs = {'a': 1}
        callback = mock.Mock()
        calls_per_secs = (1. / period)
        calls_per_secs = calls_per_secs * 0.5  # work even with delay

        timer = PeriodicTimer(period, callback, args, kwargs)

        # Run for one second
        callback.reset_mock()
        timer.start()
        time.sleep(1)
        timer.cancel()
        call_count_0 = callback.call_count

        # Wait on stopped timer for 1 second
        callback.reset_mock()
        time.sleep(1)
        call_count_1 = callback.call_count

        # Re-run for one second, multiple uses
        callback.reset_mock()
        timer.start()
        time.sleep(1)
        timer.cancel()
        call_count_2 = callback.call_count

        self.assertGreater(call_count_0, calls_per_secs)
        self.assertEquals(call_count_1, 0)
        self.assertGreater(call_count_2, calls_per_secs)

        callback.assert_called_with(*args, **kwargs)
        callback.assert_called_with(*args)

    def test_multiple_cancel(self):
        """Test multiple cancel."""
        callback = mock.Mock()
        timer = PeriodicTimer(1000, callback)
        timer.start()

        timer.cancel()
        timer.cancel()
        timer.cancel()

        self.assertEqual(0, callback.call_count)
