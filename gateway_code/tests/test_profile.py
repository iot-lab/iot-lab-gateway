# -*- coding:utf-8 -*-

""" Test profile creation with valid and invalids profiles jsons """

import unittest
import os
import re
import json
import gateway_code.profile

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) + '/'
PROFILES_DIR = CURRENT_DIR + 'profiles/'

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=too-many-public-methods
# pylint: disable=star-args


class TestsSimpleProfile(unittest.TestCase):

    def test_simple_profiles(self):

        files = [PROFILES_DIR + _json for _json in os.listdir(PROFILES_DIR)
                 if re.match("simple", _json)]

        for profile_file in files:
            with open(profile_file) as _file:
                profile_dict = json.load(_file)
                ret = gateway_code.profile.Profile(board_type='M3',
                                                   **profile_dict)
                self.assertTrue(ret.consumption is None, str(ret))

    def test_invalid_profiles(self):

        files = [PROFILES_DIR + _json for _json in os.listdir(PROFILES_DIR)
                 if re.match("invalid_simple", _json)]

        for profile_file in files:
            with open(profile_file) as _file:
                profile_dict = json.load(_file)
                self.assertRaises(Exception, gateway_code.profile.Profile,
                                  board_type='M3', **profile_dict)


class TestsConsumptionProfile(unittest.TestCase):

    def test_consumption_profiles(self):

        files = [PROFILES_DIR + _json for _json in os.listdir(PROFILES_DIR)
                 if re.match("consumption", _json)]

        for profile_file in files:
            with open(profile_file) as _file:
                profile_dict = json.load(_file)
                ret = gateway_code.profile.Profile(board_type='M3',
                                                   **profile_dict)
                self.assertTrue(ret.consumption is not None, str(ret))

    def test_invalid_profiles_consumption(self):

        files = [PROFILES_DIR + _json for _json in os.listdir(PROFILES_DIR)
                 if re.match("invalid_consumption", _json)]
        for profile_file in files:
            with open(profile_file) as _file:
                profile_dict = json.load(_file)
                self.assertRaises(Exception, gateway_code.profile.Profile,
                                  board_type='M3', **profile_dict)


class TestsRadioProfile(unittest.TestCase):

    def test_radio_profiles(self):

        files = [PROFILES_DIR + _json for _json in os.listdir(PROFILES_DIR)
                 if re.match("radio", _json)]

        for profile_file in files:
            with open(profile_file) as _file:
                profile_dict = json.load(_file)
                ret = gateway_code.profile.Profile(board_type='M3',
                                                   **profile_dict)
                self.assertTrue(ret.radio is not None, str(ret))

    def test_invalid_radio_profiles(self):

        files = [PROFILES_DIR + _json for _json in os.listdir(PROFILES_DIR)
                 if re.match("invalid_radio", _json)]
        for profile_file in files:
            with open(profile_file) as _file:
                profile_dict = json.load(_file)
                self.assertRaises(Exception, gateway_code.profile.Profile,
                                  board_type='M3', **profile_dict)


class TestsMixedProfile(unittest.TestCase):

    def test_mixed_profiles(self):
        files = [PROFILES_DIR + _json for _json in os.listdir(PROFILES_DIR)
                 if re.match("mixed", _json)]

        for profile_file in files:
            with open(profile_file) as _file:
                profile_dict = json.load(_file)
                ret = gateway_code.profile.Profile(board_type='M3',
                                                   **profile_dict)
                self.assertTrue(ret.radio is not None, str(ret))
                self.assertTrue(ret.consumption is not None, str(ret))
