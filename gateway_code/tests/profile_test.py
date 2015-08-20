# -*- coding:utf-8 -*-

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
        profile_dict = json.load(_file)
    return profile_dict


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
