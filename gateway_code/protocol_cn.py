# -*- coding:utf-8 -*-

"""
Protocol between python code and the control_node_serial_interface C code
"""


class Protocol(object):
    """
    Implements commands that can sent to the control node interface
    """

    def __init__(self, sender):
        self.sender = sender
        self.current_radio_mode = None
        self.radio_cmd_association = {
            'measure': self._config_radio_measure,
        }

    def send_cmd(self, command_list):
        """
        Send a command to the control node and wait for it's answer.
        """
        command = command_list[0]
        answer = self.sender(command_list)
        answer_valid = ([command, 'ACK'] == answer)
        return (0 if answer_valid else 1)   # 0 on success

    def start_stop(self, command, alim):
        """
        Start/stop open node

        :param command: 'start'|'stop'
        :param alim:    'dc'|'battery'
        """
        # <start|stop> <dc|battery>
        cmd = [command, alim]
        return self.send_cmd(cmd)

    def reset_time(self):
        """
        Reset time on control node

        Also updates our time reference in the C code
        """
        # reset_time
        cmd = ['reset_time']
        return self.send_cmd(cmd)

    def green_led_blink(self):
        """ Set green led in blinking mode """
        cmd = ['green_led_blink']
        return self.send_cmd(cmd)

    def green_led_on(self):
        """ Set green led on """
        # reset_time
        cmd = ['green_led_on']
        return self.send_cmd(cmd)

    def config_consumption(self, consumption=None):
        """
        Configure consumption measures on control node

        :param consumption: consumption measures configuration
        :type consumption:  class profile._Consumption
        """
        # config_consumption_measure
        #     <stop>
        #     <start> <3.3V|5V|BATT> p <0|1> v <0|1> c <0|1>
        #         -p <periods_see_c_code> -a <average_see_c_code>

        cmd = ['config_consumption_measure']
        if consumption is None or \
                not (consumption.power or consumption.voltage or
                     consumption.current):
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
        """
        Configure radio measures on control node
        :param radio: radio configuration
        :type radio:  class Radio

        It stops previous radio measures if necessary
        """
        ret = 0

        # stop current radio
        ret_val = self._stop_radio_if_required(radio)
        if 0 != ret_val:
            return ret_val

        if radio is None:
            # no config, Finished
            return 0

        # channel config
        ret += self._config_radio_signal(radio)

        # radio mode config
        ret += self._config_radio_mode(radio)

        return ret

    def _config_radio_signal(self, radio):
        """
        Configure radio signal: tx power and channel
        """
        # config_radio_signal <power> <channel>
        cmd = ['config_radio_signal']
        cmd.append(str(radio.power))
        cmd.append(str(radio.channel))
        ret = self.send_cmd(cmd)
        return ret

    def _config_radio_mode(self, radio):
        """
        Configure the appropriate radio mode
        """
        ret = None
        if 'measure' == radio.mode:
            ret = self._config_radio_measure("start", radio.frequency)
        else:
            raise NotImplementedError("Uknown radio mode: %s", radio.mode)

        # update radio mode
        if 0 == ret:
            self.current_radio_mode = radio.mode
        return ret

    def _config_radio_measure(self, command="stop", frequency=None):
        """
        Configure radio measure
        """
        # config_radio_signal
        #     <stop>
        #     <start> <frequency>
        cmd = ['config_radio_measure']
        cmd.append(command)
        if "start" == command:
            cmd.append(str(frequency))

        ret = self.send_cmd(cmd)
        return ret

    def _stop_radio_if_required(self, radio):
        """
        Stop the radio if current mode and new mode are not the same
        """

        # is radio running
        if self.current_radio_mode is None:
            return 0

        # is new mode the same as current mode
        if radio is not None and self.current_radio_mode == radio.mode:
            return 0

        # stop current mode
        ret = self.radio_cmd_association[self.current_radio_mode]()
        if ret == 0:
            self.current_radio_mode = None

        return ret
