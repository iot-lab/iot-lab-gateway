# -*- coding:utf-8 -*-

"""

Profile module, implementing the 'Profile' class
and methods to convert it to config commands

"""

import recordtype

# Disable: I0011 - 'locally disabling warning'
# Disable: C0103 - Invalid name 'CamelCase' -> represents a class
#pylint:disable=I0011,C0103

Consumption = recordtype.recordtype('consumption',
        ['source', 'period', 'average',
            ('power', False), ('voltage', False), ('current', False), ])

Profile     = recordtype.recordtype('profile',
        ['profilename', 'power', ('consumption', None)]) #, ('radio', None)]

#  class Radio:
#      """
#      Class Radio configuration  for Control Node
#      """
#      def __init__(self, rssi=None, frequency=None):
#          self.rssi = rssi
#          self.frequency = frequency



def profile_from_dict(json_dict):
    """
    Create a profile from json extracted dictionary
    """
    profile_args = {}

    string_args = ('profilename', 'power')
    class_args  = (('consumption', Consumption),) # ('radio', Radio)


    # Extract 'string arguments' from dictionary 'as is'
    #     dict comprehensions not allowed before Python 2.7
    #     using dict.update with iterable on (key/value tuple)
    try:
        string_args_list = [(arg, json_dict[arg]) for arg in string_args]
    except KeyError as ex:
        raise ValueError("Missing entry: %r" % ex.args[0])


    profile_args.update(string_args_list)


    # Extract existing arguments and initialize their class
    for name, obj_class in class_args:
        if name in json_dict:
            try:
                profile_args[name] = obj_class(**json_dict[name])
            except TypeError as ex:
                raise ValueError("Invalid arguments in %r field" % name)


    # then create the final Profile object
    profile = Profile(**profile_args)

    return profile

