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

        # Extract 'string arguments' from dictionary 'as is'
        #     dict comprehensions not allowed before Python 2.7
        #     using dict.update with iterable on (key/value tuple)
        _str_args = ('profilename', 'power')
        try:
            _str_args_list = [(arg, profile_dict[arg]) for arg in _str_args]
            profile_args.update(_str_args_list)
        except KeyError as ex:
            # these entries are required
            raise ValueError("Missing entry: %r" % ex.args[0])

        # add consumption (it needs power_source and board_type)
        try:
            profile_args['consumption'] = Consumption(
                power_source=profile_dict['power'],  # add power source
                board_type=board_type,
                **profile_dict['consumption'])
        except KeyError:
            pass  # 'consumption' not in profile

        # add radio
        try:
            profile_args['radio'] = Radio(**profile_dict['radio'])
        except KeyError:
            pass  # 'radio' not in profile

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
            raise ValueError


_RADIO_TYPE = recordtype('radio', ['power', 'channel', 'mode',
                                   ('freq', None)])


class Radio(_RADIO_TYPE):
    """
    Radio monitoring configuration
    """

    def __init__(self, *args, **kwargs):
        self.power = None
        self.channel = None
        self.mode = None
        self.freq = None
        try:
            _RADIO_TYPE.__init__(self, *args, **kwargs)
        except TypeError:
            raise ValueError

        self._is_valid()

    def _is_valid(self):
        """
        raise ValueError if self is not a 'valid' configuration
        """
        if self.mode == "measure" and self.freq is None:
            raise ValueError
