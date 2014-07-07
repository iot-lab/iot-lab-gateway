# -*- coding:utf-8 -*-

"""
Profile module, implementing the 'Profile' class
and methods to convert it to config commands
"""

# Disable: I0011 - 'locally disabling warning'
# Disable: R0903 - Too few public methods
# Disable: R0913 - Too many arguments (%d/5)
# pylint: disable=I0011,R0903,R0913


class Profile(object):
    """ Experiment monitoring Profile """

    def __init__(self, profilename, power, board_type,
                 consumption=None, radio=None):
        self.profilename = profilename
        self.power = power

        self.consumption = None
        self.radio = None

        _current = None
        try:
            # add consumption (it needs power_source and board_type)
            if consumption is not None:
                _current = 'consumption'
                self.consumption = Consumption(
                    source=power, board_type=board_type, **consumption)
            # add radio
            if radio is not None:
                _current = 'radio'
                self.radio = Radio(**radio)

        except TypeError:
            raise ValueError("Error in %s arguments" % _current)


class Consumption(object):
    """ Consumption monitoring configuration """
    consumption_source = {
        ('M3', 'dc'): '3.3V',
        ('A8', 'dc'): '5V',
        ('M3', 'battery'): 'BATT',
        ('A8', 'battery'): 'BATT',
    }

    def __init__(self, source, board_type, period, average,
                 power=False, voltage=False, current=False):
        self.source = self.consumption_source[(board_type, source)]
        self.period = period
        self.average = average

        self.power = power
        self.voltage = voltage
        self.current = current


class Radio(object):
    """ Radio monitoring configuration """

    def __init__(self, mode, channels, period=None, num_per_channel=None):
        # power=None, pkt_size=None

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
        if 0 == len(self.channels):
            raise ValueError
        # all channels must be in [11, 26]
        if len(set(self.channels) - set(range(11, 26 + 1))):
            raise ValueError("Radio->channels %r:" % self.channels)

        #
        # Mode
        #
        # RSSI
        if self.mode == "rssi":
            if self.period not in range(1, 2**16):
                raise ValueError("Radio->rssi->period %r" % self.period)
            if self.num_per_channel is None:
                raise ValueError("Radio->rssi->num_per_channel %r" %
                                 self.num_per_channel)
        # Sniffer
        elif self.mode == "sniffer":
            if self.period is None:
                self.period = 0
            if self.period not in range(0, 2**16):
                raise ValueError("Radio->sniffer->period %r" % self.period)

            # There should only be a period if there are many channels
            if ((self.period == 0) and (len(self.channels) != 1) or
                    (self.period != 0) and (len(self.channels) == 1)):
                raise ValueError("Radio->sniffer->period/channels %r %r" %
                                 (self.period, self.channels))

        # Error
        else:
            raise ValueError("Radio->mode %r" % self.mode)
