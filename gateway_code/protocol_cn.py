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

    def _send_cmd(self, command_list):
        """
        Send a command to the control node and wait for it's answer.
        """
        command = command_list[0]
        import sys
        print >> sys.stderr, 'Sent pkt: %s' % command_list
        answer = self.sender(command_list)
        print >> sys.stderr, 'Rec pkt:  %r' % answer

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
        return self._send_cmd(cmd)


    def reset_time(self):
        """
        Reset time on control node
            Updates our time reference in the C code
        """
        # reset_time
        cmd = ['reset_time']
        return self._send_cmd(cmd)

    def config_consumption(self, consumption=None):
        """
        Configure consumption measures on control node
        :param consumption: consumption configuration
        :type consumption:  class Consumption
        """
        # config_consumption_measure
        #     <stop>
        #     <start> <3.3V|5V|BATT> p <0|1> v <0|1> c <0|1>
        #         -p <periods_see_c_code> -a <average_see_c_code>

        cmd = ['config_consumption_measure']
        if consumption is None or not (consumption.power or \
                consumption.voltage or consumption.current): #pragma: no cover
            cmd.append('stop')
        else:
            cmd.append('start')
            cmd.append(consumption.source)
            cmd.extend(['p', str(int(consumption.power))])
            cmd.extend(['v', str(int(consumption.voltage))])
            cmd.extend(['c', str(int(consumption.current))])
            cmd.extend(['-p', consumption.period])
            cmd.extend(['-a', consumption.average])
        ret = self._send_cmd(cmd)
        return ret
