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


""" Test profile creation with valid and invalids profiles jsons """

import unittest
import os
import re
import json
from gateway_code.profile import Profile
from gateway_code.open_nodes.node_m3 import NodeM3

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) + '/'
PROFILES_DIR = CURRENT_DIR + 'profiles/'

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=no-member


def profile_dict(file_path):
    with open(file_path) as _file:
        prof_d = json.load(_file)
    return prof_d


class TestsSimpleProfile(unittest.TestCase):

    def test_simple_profiles(self):

        files = [PROFILES_DIR + _json for _json in os.listdir(PROFILES_DIR)
                 if re.match("simple", _json)]

        for profile_file in files:
            ret = Profile.from_dict(NodeM3, profile_dict(profile_file))
            self.assertTrue(ret.consumption is None, str(ret))

    def test_invalid_profiles(self):

        files = [PROFILES_DIR + _json for _json in os.listdir(PROFILES_DIR)
                 if re.match("invalid_simple", _json)]

        for profile_file in files:
            self.assertRaises(ValueError, Profile.from_dict,
                              NodeM3, profile_dict(profile_file))

    def test_profile_from_dict_empty(self):
        self.assertIsNone(Profile.from_dict(NodeM3, None))


class TestsConsumptionProfile(unittest.TestCase):

    def test_consumption_profiles(self):

        files = [PROFILES_DIR + _json for _json in os.listdir(PROFILES_DIR)
                 if re.match("consumption", _json)]

        for profile_file in files:
            ret = Profile.from_dict(NodeM3, profile_dict(profile_file))
            self.assertTrue(ret.consumption is not None, str(ret))

    def test_invalid_profiles_consumption(self):

        files = [PROFILES_DIR + _json for _json in os.listdir(PROFILES_DIR)
                 if re.match("invalid_consumption", _json)]
        for profile_file in files:
            self.assertRaises(ValueError, Profile.from_dict,
                              NodeM3, profile_dict(profile_file))


class TestsRadioProfile(unittest.TestCase):

    def test_radio_profiles(self):

        files = [PROFILES_DIR + _json for _json in os.listdir(PROFILES_DIR)
                 if re.match("radio", _json)]

        for profile_file in files:
            ret = Profile.from_dict(NodeM3, profile_dict(profile_file))
            self.assertTrue(ret.radio is not None, str(ret))

    def test_invalid_radio_profiles(self):

        files = [PROFILES_DIR + _json for _json in os.listdir(PROFILES_DIR)
                 if re.match("invalid_radio", _json)]
        for profile_file in files:
            self.assertRaises(ValueError, Profile.from_dict,
                              NodeM3, profile_dict(profile_file))


class TestsMixedProfile(unittest.TestCase):

    def test_mixed_profiles(self):
        files = [PROFILES_DIR + _json for _json in os.listdir(PROFILES_DIR)
                 if re.match("mixed", _json)]

        for profile_file in files:
            ret = Profile.from_dict(NodeM3, profile_dict(profile_file))
            self.assertTrue(ret.radio is not None, str(ret))
            self.assertTrue(ret.consumption is not None, str(ret))
