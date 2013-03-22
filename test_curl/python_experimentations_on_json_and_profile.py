#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json

FILE = 'profile.json'


# >>> import json
# >>> def as_complex(dct):
# ...     if '__complex__' in dct:
# ...         return complex(dct['real'], dct['imag'])
# ...     return dct
# ...
# >>> json.loads('{"__complex__": true, "real": 1, "imag": 2}',
# ...     object_hook=as_complex)
# (1+2j)
# >>> import decimal
# >>> json.loads('1.1', parse_float=decimal.Decimal)
# Decimal('1.1')
#
#
# >>> import json
# >>> class ComplexEncoder(json.JSONEncoder):
# ...     def default(self, obj):
# ...         if isinstance(obj, complex):
# ...             return [obj.real, obj.imag]
# ...         return json.JSONEncoder.default(self, obj)
# ...
# >>> json.dumps(2 + 1j, cls=ComplexEncoder)
# '[2.0, 1.0]'
# >>> ComplexEncoder().encode(2 + 1j)
# '[2.0, 1.0]'
# >>> list(ComplexEncoder().iterencode(2 + 1j))
# ['[2.0', ', 1.0', ']']

class Profile(object):

    def __init__(self, test):
        self.test = test


class Consumption(object):

    def __init__(self, current, voltage, power, frequency):
        self.current = current
        self.voltage = voltage
        self.power = power
        self.frequency = frequency

class Radio(object):
    def __init__(self, rssi, frequency):
        self.rssi = rssi
        self.frequency = frequency

class Sensor(object):

    def __init__(self, temperature, luminosity, frequency):
        self.temperature = temperature
        self.luminosity = luminosity
        self.frequency = frequency



class Profile(object):

    @classmethod
    def profile_from_dict(cls, json_dict):
        simple_args = ('profilename', 'power')
        class_correspondance = (('sensor', Sensor), ('radio', Radio),
                ('consumption', Consumption))

        # simple arguments
        args = {name:json_dict[name] for name in simple_args if name in json_dict}
        # class arguments
        for name, obj_class in class_correspondance:
            if name in json_dict:
                args[name] = obj_class(**dict[name])


        profile = Profile(**args)
        return profile

    def __init__(self, profilename=None, power=None, consumption=None, radio=None, sensor=None):
        self.profilename = profilename
        self.power = power
        self.consumption = consumption
        self.radio = radio
        self.sensor = sensor



Profile(profilename='auieau', power='auiauie')
Profile(**{'profilename':'auieau', 'power':'auie'})



FILE_1 = """
{
    "consumption": {
        "current": true,
        "frequency": 5000,
        "power": false,
        "voltage": true
    },
    "power": "battery",
    "profilename": "test_profile",
    "radio": {
        "frequency": 5000,
        "rssi": true
    },
    "sensor": {
        "frequency": 30000,
        "luminosity": false,
        "temperature": true
    }
}
"""


FILE_2 = """
{
    "power": "battery",
    "profilename": "test_profile",
    "sensor": {
        "frequency": 30000,
        "luminosity": false,
        "temperature": true
    }
}
"""

for profile_json in (FILE_1, FILE_2):
    print profile_json
    json_dict = json.loads(profile_json)

    profile_object = Profile.profile_from_dict(json_dict)


    print "Object : %s" % profile_object
    print "obj.profilename : %s" % profile_object.profilename
    print "obj.power : %s" % profile_object.power
    print "obj.consumption : %s" % profile_object.consumption
    print "obj.radio : %s" % profile_object.radio
    print "obj.sensor : %s" % profile_object.sensor


