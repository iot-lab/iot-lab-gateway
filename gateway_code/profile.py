# -*- coding:utf-8 -*-

"""
Profile module, implementing the 'Profile' class
and methods to convert it to config commands
"""

# pylint:disable=too-many-arguments,too-few-public-methods


class Profile(object):
    """ Experiment monitoring Profile """

    def __init__(self, open_node_type,  # pylint:disable=unused-argument
                 profilename, power,
                 consumption=None, radio=None, **_kwargs):
        self.profilename = profilename
        self.power = power

        self.consumption = None
        self.radio = None

        _current = None
        try:
            # add consumption (it needs power_source and alim)
            if consumption is not None:
                _current = 'consumption'
                self.consumption = Consumption(open_node_type.ALIM,
                                               source=power, **consumption)
            # add radio
            if radio is not None:
                _current = 'radio'
                self.radio = Radio(**radio)

        except TypeError as err:
            assert False, "Error in %s arguments %r" % (_current, err)


class Consumption(object):
    """ Consumption monitoring configuration """
    choices = {
        'consumption': {
            'period': [140, 204, 332, 588, 1100, 2116, 4156, 8244],
            'average': [1, 4, 16, 64, 128, 256, 512, 1024]},
        'alim': ('3.3V', '5V'),
    }

    def __init__(self, alim, source, period, average,
                 power=False, voltage=False, current=False):
        _err = "Required values period/average for consumption measure."
        assert period is not None and average is not None, _err
        period = int(period)
        average = int(average)

        assert period in self.choices['consumption']['period']
        assert average in self.choices['consumption']['average']
        assert alim in self.choices['alim']

        self.source = alim if source == 'dc' else 'BATT'
        self.period = period
        self.average = average

        self.power = power
        self.voltage = voltage
        self.current = current


class Radio(object):
    """ Radio monitoring configuration """
    choices = {
        'radio': {'channels': range(11, 27)},
        'rssi': {'num_per_channel': range(0, 256), 'period': range(1, 2**16)},
        'sniffer': {'period': range(0, 2**16)}
    }

    def __init__(self, mode, channels, period=None, num_per_channel=None):
        # power=None, pkt_size=None
        assert len(channels)
        for channel in channels:
            assert channel in self.choices['radio']['channels']

        self.mode = mode
        self.channels = channels
        self.period = period

        # RSSI + Injection
        self.num_per_channel = num_per_channel

        # Noise + Injection
        # self.power = None
        # Injection
        # self.pkt_size = None

        self._is_valid()

    def _is_valid(self):
        """ raise ValueError if self is not a 'valid' configuration """

        # Channels not empty
        # all channels must be in [11, 26]

        #
        # Mode
        #
        # RSSI
        if self.mode == "rssi":
            _err = "Required 'channels/period' for radio rssi measure"
            assert self.period is not None and self.channels is not None, _err

            # num_per_channels is required when multiple channels are given
            _err = "Required 'num_per_channels' as multiple channels provided"
            assert len(self.channels) == 1 or self.num_per_channel != 0, _err
            assert self.period in self.choices['rssi']['period']
            assert self.num_per_channel in \
                self.choices['rssi']['num_per_channel']

        # Sniffer
        elif self.mode == "sniffer":
            self.period = self.period or 0

            # num_per_channels is required when multiple channels are given
            _err = "Required 'period' as multiple channels provided"

            assert self.period in self.choices['sniffer']['period']
            # period only if there are more than 1 channel
            assert bool(self.period) == (len(self.channels) != 1)
            assert self.num_per_channel is None

        assert self.mode in ('rssi', 'sniffer')
