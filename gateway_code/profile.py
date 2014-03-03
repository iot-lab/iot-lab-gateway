# -*- coding:utf-8 -*-

"""
Profile module, implementing the 'Profile' class
and methods to convert it to config commands

"""

from recordtype import recordtype

# Disable: I0011 - 'locally disabling warning'
# Disable: R0903 - Too few public methods
# pylint: disable=I0011,R0903


_PROFILE_TYPE = recordtype('profile', ['profilename', 'power',
                                       ('consumption', None), ('radio', None)])


class Profile(_PROFILE_TYPE):
    """
    Experiment monitoring Profile
    """

    def __init__(self, profile_dict, board_type):
        self.profilename = None
        self.power = None
        self.consumption = None
        self.radio = None

        profile_args = {}

        # Extract 'string arguments' from dictionary 'as is' (Required entries)
        _str_args = ('profilename', 'power')
        try:
            profile_args = {arg: profile_dict[arg] for arg in _str_args}
        except KeyError as ex:
            raise ValueError("Missing entry: %r" % ex.args[0])

        # add consumption (it needs power_source and board_type)
        if profile_dict.get('consumption') is not None:
            profile_args['consumption'] = Consumption(
                power_source=profile_dict['power'],
                board_type=board_type,
                **profile_dict['consumption'])

        # add radio
        if profile_dict.get('radio') is not None:
            profile_args['radio'] = Radio(**profile_dict['radio'])

        # then create the final Profile object
        _PROFILE_TYPE.__init__(self, **profile_args)


CONSUMPTION_SOURCE = {
    ('M3', 'dc'): '3.3V',
    ('A8', 'dc'): '5V',
    ('M3', 'battery'): 'BATT',
    ('A8', 'battery'): 'BATT',
}

_CONSUMPTION_TYPE = recordtype('consumption',
                               ['source', 'period', 'average',
                                ('power', False), ('voltage', False),
                                ('current', False), ])


class Consumption(_CONSUMPTION_TYPE):
    """
    Consumption monitoring configuration
    """

    def __init__(self, power_source, board_type, *args, **kwargs):
        self.source = None
        self.period = None
        self.average = None

        self.power = None
        self.voltage = None
        self.current = None

        # add measure source from power and board_type
        _source = CONSUMPTION_SOURCE[(board_type, power_source)]

        try:
            _CONSUMPTION_TYPE.__init__(self, source=_source, *args, **kwargs)
        except TypeError:
            raise ValueError("Error in consumption arguments")


_RADIO_TYPE = recordtype('radio', ['mode', 'channels', 'period',
                                   ('num_per_channel', None),
                                   ('power', None),
                                   ('pkt_size', None)])


class Radio(_RADIO_TYPE):
    """
    Radio monitoring configuration
    """

    def __init__(self, *args, **kwargs):
        self.mode = None
        self.channels = None
        self.period = None

        self.num_per_channel = None

        self.power = None

        self.pkt_size = None
        try:
            _RADIO_TYPE.__init__(self, *args, **kwargs)
        except TypeError:
            raise ValueError

        self._is_valid()

    def _is_valid(self):
        """ raise ValueError if self is not a 'valid' configuration """

        if 0 == len(self.channels):
            raise ValueError
        # all channels must be in [11, 26]
        if len(set(self.channels) - set(range(11, 26 + 1))):
            raise ValueError

        if self.period not in range(1, 2**16):
            raise ValueError

        if self.mode == "rssi":
            if self.num_per_channel is None:
                raise ValueError

        # invalid measures types (at the end for coverage issue)
        if self.mode not in ["rssi"]:
            raise ValueError
