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

# pylint: disable=missing-docstring
# pylint <= 1.3
# pylint: disable=too-many-public-methods
# pylint >= 1.4
# pylint: disable=too-few-public-methods
# pylint: disable=no-member

import unittest
from subprocess import CalledProcessError

import mock
import pytest

from gateway_code.autotest import open_a8_interface


class TestA8Connection(unittest.TestCase):
    def test_connection_error(self):
        error = open_a8_interface.A8ConnectionError("value", "err_msg")
        self.assertEquals("'value' : 'err_msg'", str(error))

    @mock.patch('gateway_code.autotest.open_a8_interface.OpenA8Connection.scp')
    def test_flash_error(self, scp):
        scp.side_effect = CalledProcessError(1, 'flash', 'flash failed')
        connection = open_a8_interface.OpenA8Connection()
        assert connection.flash('test/firmware') == 1
