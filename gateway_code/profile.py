# -*- coding:utf-8 -*-
import json

class Consumption:
    """
    Class Consumption configuration for Control Node polling

    """
    def __init__(self, current=None, voltage=None, power=None, frequency=None):
        self.current = current
        self.voltage = voltage
        self.power = power
        self.frequency = frequency

class Radio:
    """
    Class Radio configuration  for Control Node polling

    """
    def __init__(self, rssi=None, frequency=None):
        self.rssi = rssi
        self.frequency = frequency

class Profile:
    """
    Class Profile configuration for Control Node polling

    """
    def __init__(self, profilename=None, power=None, consumption=None, radio=None):
        self.profilename = profilename
        self.power = power
        self.consumption = consumption
        self.radio = radio

class ProfileJSONDecoder(json.JSONDecoder):
    """ 
    Converts a json string profile configuration into python object Profile

    """   
    def decode(self, profile_json):
        # convert string to dict
        json_dict = json.loads(profile_json)

        simple_args = ('profilename', 'power')
        class_mapping = (('radio', Radio),
                ('consumption', Consumption))

        # simple arguments
        args = {}
        for name in simple_args:
            if name in json_dict:
                args[name] = json_dict[name]
        #args = {name:json_dict[name] for name in simple_args if name in json_dict}
        # class arguments
        for name, obj_class in class_mapping:
            if name in json_dict:
                args[name] = obj_class(**json_dict[name])
        profile = Profile(**args)
        return profile

