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


""" Protocol between python code and control_node_serial_interface C code """


class Protocol(object):
    """ Implements commands that can be sent to control node interface """

    def __init__(self, sender):
        self.sender = sender

    def send_cmd(self, command_list):
        """ Send a command to the control node and wait for it's answer.  """
        command = command_list[0]
        answer = self.sender(command_list)
        answer_valid = ([command, 'ACK'] == answer)
        return 0 if answer_valid else 1   # 0 on success

    def start_stop(self, command, alim):
        """ Start/stop open node

        :param command: 'start'|'stop'
        :param alim:    'dc'|'battery'
        """
        # <start|stop> <dc|battery>
        cmd = [command, alim]
        return self.send_cmd(cmd)

    def set_time(self):
        """ Set unix time on control node """
        # set_time
        cmd = ['set_time']
        return self.send_cmd(cmd)

    @staticmethod
    def _set_node_id_args(node_id):
        """
        >>> Protocol._set_node_id_args('m3-1')
        ('m3', '1')

        >>> Protocol._set_node_id_args('a8-256')
        ('a8', '256')

        >>> Protocol._set_node_id_args('m3-00-ci')
        ('m3', '0')
        """
        archi, num_str = node_id.split('-')[0:2]
        num = str(int(num_str))
        return archi, num

    def set_node_id(self, node_id):
        """ Set node id on control node"""
        # set_node_id
        archi, num = self._set_node_id_args(node_id)

        # Other nodes types are not handled by the protocol (Leonardo, Fox)
        if archi not in ('m3', 'a8'):
            return 0

        cmd = ['set_node_id', archi, num]
        return self.send_cmd(cmd)

    def green_led_blink(self):
        """ Set green led in blinking mode """
        cmd = ['green_led_blink']
        return self.send_cmd(cmd)

    def green_led_on(self):
        """ Set green led on """
        cmd = ['green_led_on']
        return self.send_cmd(cmd)

    def config_consumption(self, consumption=None):
        """ Configure consumption measures on control node

        :param consumption: consumption measures configuration
        :type consumption:  class profile._Consumption
        """
        # config_consumption_measure
        #     <stop>
        #     <start> <3.3V|5V|BATT> p <0|1> v <0|1> c <0|1>
        #         -p <periods_see_c_code> -a <average_see_c_code>

        cmd = ['config_consumption_measure']
        if (consumption is None or
                not (consumption.power or consumption.voltage or
                     consumption.current)):
            cmd.append('stop')
        else:
            cmd.append('start')
            cmd.append(consumption.source)
            cmd.extend(['p', str(int(consumption.power))])
            cmd.extend(['v', str(int(consumption.voltage))])
            cmd.extend(['c', str(int(consumption.current))])
            cmd.extend(['-p', str(consumption.period)])
            cmd.extend(['-a', str(int(consumption.average))])
        ret = self.send_cmd(cmd)
        return ret

    def config_radio(self, radio):
        """ Configure radio measures on control node

        :param radio: radio configuration
        :type radio:  class Radio

        It stops previous radio measures if necessary """

        if radio is None:
            return self._stop_radio()

        if radio.mode == 'rssi':
            return self._config_radio_measure(radio)
        elif radio.mode == 'sniffer':
            return self._config_radio_sniffer(radio)

        raise NotImplementedError("Uknown radio mode: {}".format(radio.mode))

    def _config_radio_measure(self, radio):
        """ Configure radio measure """
        # config_radio_measure
        #     <channel,list,comma,separated>
        #     <period>
        #     <num_measure_per_channel>
        sorted_channels = sorted(list(set(radio.channels)))

        cmd = ['config_radio_measure']
        cmd.append(','.join(str(x) for x in sorted_channels))
        cmd.append(str(radio.period))
        cmd.append(str(radio.num_per_channel))

        ret = self.send_cmd(cmd)
        return ret

    def _config_radio_sniffer(self, radio):
        """ Configure radio sniffer """
        # config_radio_sniffer
        #     <channel,list,comma,separated>
        #     <period>
        sorted_channels = sorted(list(set(radio.channels)))

        cmd = ['config_radio_sniffer']
        cmd.append(','.join(str(x) for x in sorted_channels))
        cmd.append(str(radio.period))

        ret = self.send_cmd(cmd)
        return ret

    def _stop_radio(self):
        """ Stop the radio """
        return self.send_cmd(['config_radio_stop'])
