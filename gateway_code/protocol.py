# -*- coding:utf-8 -*-
"""
Protocol between gateway and control node

Packet send format
SYNC_BYTE | LEN | TYPE | -?-?-?-?-




Measures Config packet format
SYNC_BYTE | LEN | TYPE | MEASURE_SOURCES | MEASURE_CONFIG

Measures values packet format
SYNC_BYTE | LEN | TYPE | MEASURE_SOURCES | Measures_count | [TIME | Values ]*|

"""

import gateway_code.profile
from datetime import timedelta, datetime


SYNC_BYTE = chr(0x80)

ACK  = chr(0x0A)
NACK = chr(0x02)

TIME_FACTOR = 32768

TYPE_MEASURES_MASK = 0xF0


#
# TYPE of packets
#

# Commands
TYPE_CMD_OPEN_NODE_START = chr(0x70)
TYPE_CMD_OPEN_NODE_STOP  = chr(0x71)
BATT = chr(0x0)
DC   = chr(0x1)
TYPE_CMD_RESET_TIME = chr(0x72)

# Config measures
TYPE_CMD_CONFIG_MEASURES_CONSUMPTION = chr(0x79)
# TYPE_CMD_CONFIG_MEASURES_RADIO = ?
# TYPE_CMD_CONFIG_MEASURES_SNIFFER = ?
# TYPE_CMD_CONFIG_RADIO_NOISE = ? -> no monitoring values
# TYPE_CMD_CONFIG_FAKE_SENSOR = ?


#
# Measures packets
#


# Consumption measures

TYPE_MEASURES_CONSUMPTION = chr(0xFF)
# Measures sources flags
# may be the 3 following
CONSUMPTION_POWER   = 1 << 0
CONSUMPTION_VOLTAGE = 1 << 1
CONSUMPTION_CURRENT = 1 << 2
# nothing on bit 3
# Only one of the following
CONSUMPTION_3_3V    = 1 << 4
CONSUMPTION_5V      = 1 << 5
CONSUMPTION_BATT    = 1 << 6
# nothing on bit 7

POWER_MEASURES = {
        'power'   : CONSUMPTION_POWER,
        'voltage' : CONSUMPTION_VOLTAGE,
        'current' : CONSUMPTION_CURRENT,
        }
POWER_SOURCE = {
        '3.3V' : CONSUMPTION_3_3V,
        '5V'   : CONSUMPTION_5V,
        'BATT' : CONSUMPTION_BATT,
        }
POWER_SOURCE_VAL = dict([(POWER_SOURCE[key], key) \
        for key in POWER_SOURCE])


# CONFIG BYTE == [ PERIOD | AVERAGE << 4 | ENABLE(BIT7) ]
INA226_PERIOD = {
        '140us' : 0,
        '204us' : 1,
        '332us' : 2,
        '588us' : 3,
        '1100us': 4,
        '2116us': 5,
        '4156us': 6,
        '8244us': 7,
        }
INA226_AVERAGE = {
        '1'    : 0,
        '4'    : 1,
        '16'   : 2,
        '64'   : 3,
        '128'  : 4,
        '256'  : 5,
        '512'  : 6,
        '1024' : 7,
        }
INA226_ENABLE        = 1 << 7
INA226_DISABLE       = 0 << 7
INA226_STATE = {
        'start': INA226_ENABLE,
        'stop': INA226_DISABLE,
        }



COMMAND = {'start': TYPE_CMD_OPEN_NODE_START, 'stop': TYPE_CMD_OPEN_NODE_STOP, \
        'reset_time': TYPE_CMD_RESET_TIME, \
        'consumption': TYPE_CMD_CONFIG_MEASURES_CONSUMPTION}
ALIM    = {'battery': BATT, 'dc': DC,}


def _str_packet(info, data):
    """
    Debug function that prints a packet

    >>> _str_packet('Msg', chr(0x20) + chr(0xFF))
    "Msg: '20 FF '"

    >>> _str_packet('Info', None)
    "Info: 'None'"

    """
    debug_out = info + ": '"
    if data is None:
        debug_out += str(None)
    else:
        for i in data:
            debug_out += '%02X ' % ord(i)

    debug_out += "'"
    return debug_out

def _valid_result_command(packet, pkt_type):
    """
    Validate type of packet,
    ACK/NACK

    >>> _valid_result_command(chr(0x42) + ACK, chr(0x42))
    0

    >>> _valid_result_command(chr(0x42) + NACK, chr(0x42))
    1
    >>> _valid_result_command(chr(0x42) + ACK, chr(0x66))
    1
    >>> _valid_result_command(None, '')
    1

    """

    if packet is None:
        ret_b = False
    else:
        ret_b = True
        ret_b &= (packet[0] == pkt_type)
        ret_b &= (packet[1] == ACK)

    ret   = 0 if ret_b else 1
    return ret


class Protocol(object):
    """
    Class protocol containing current configuration for packets reception
    """

    def __init__(self, sender):

        self.sender   = sender
        self.time     = None
        self.new_time = None

        self.conso_conf = {}

        self.measures_decode = {
                chr(0xFF): self.decode_consumption_pkt,
                }

    def send_cmd(self, data):
        """
        Send a command to the control node and wait for it's answer.
        """

        import sys
        print >> sys.stderr, _str_packet('Sent packet', data)
        result = self.sender(data)
        print >> sys.stderr, _str_packet('Rec packet', data)

        return result


    def start_stop(self, command, alim):
        """
        Start or stop open node via the control node and use given alim.
        """

        command_b = COMMAND[command]
        alim_b    = ALIM[alim]
        data      = command_b + alim_b

        result = self.send_cmd(data)

        ret = _valid_result_command(result, command_b)
        return ret

    def reset_time(self, command):
        """
        Reset the time reference on the control node at 0
        """

        command_b = COMMAND[command]
        data      = command_b

        result = self.send_cmd(data)

        ret = _valid_result_command(result, command_b)
        return ret


    def config_consumption(self, consumption=None):
        """
        Configure consumption measures

        :param consumption: the consumption object
        :type consumption: gateway_code.profile.Consumption
        """

        command_b     = COMMAND['consumption']
        measures_flag = 0
        config_flag   = 0

        if (consumption is None):
            # stop consumption measures
            config_flag |= INA226_STATE['stop']
        elif not (consumption.power or consumption.voltage or \
                consumption.current): #pragma: no cover
            # no values asked, disable
            # stop consumption measures
            config_flag |= INA226_STATE['stop']
        else:
            # start and configure consumption
            for measure in 'power', 'voltage', 'current':
                if getattr(consumption, measure):
                    measures_flag |= POWER_MEASURES[measure]
            measures_flag |= POWER_SOURCE[consumption.source]

            config_flag |= INA226_PERIOD[consumption.period]
            config_flag |= INA226_AVERAGE[consumption.average] << 4
            config_flag |= INA226_STATE['start']


        data = command_b + chr(measures_flag) + chr(config_flag)
        result = self.send_cmd(data)

        ret = _valid_result_command(result, command_b)
        return ret




    def decode_measure_packet(self, pkt):
        """
        Generic measure decoding function.
        Calls the appropriate function for each type.
        """
        measure_type = pkt[0]
        try:
            ret = self.measures_decode[measure_type](pkt)
        except KeyError: #pragma: no cover
            from sys import stderr # TODO replace with logger
            print >> stderr, 'Uknown measure packet: %02X' % ord(measure_type)
            ret = None

        return ret


    def update_consumption_config(self, config_byte):
        """
        Update the current configuration for consumption decoding
        """

        self.conso_conf['source'] = POWER_SOURCE_VAL[config_byte & 0x70]

        self.conso_conf['measures'] = ['t'] + \
            (['p'] if config_byte & CONSUMPTION_POWER else []) + \
            (['v'] if config_byte & CONSUMPTION_VOLTAGE else []) + \
            (['c'] if config_byte & CONSUMPTION_CURRENT else [])
        _num_measures = len(self.conso_conf['measures']) - 1 # without time


        # Time = uint, values = float
        self.conso_conf['len']        = 4    + _num_measures * 4
        self.conso_conf['unpack_str'] = '!L' + _num_measures * 'f'


    def decode_consumption_pkt(self, pkt):
        """
        Extract measures stored in pkt.
        """
        from struct import unpack

        header_size = 3
        config = ord(pkt[1])
        count  = ord(pkt[2])

        # decode current frame content
        # TODO remove after ack update
        self.update_consumption_config(config)


        assert len(pkt) == header_size + count * self.conso_conf['len']
        # extract list of raw measures from payload
        chunks = [pkt[start:start + self.conso_conf['len']] for start in \
                range(header_size, len(pkt), self.conso_conf['len'])]
        assert len(chunks) == count


        # extract the 'count' measures
        all_measures = []
        for raw_measure in chunks:
            measures = list(unpack(self.conso_conf['unpack_str'], raw_measure))
            # convert tick to seconds + time reference
            measures[0] = self.time + timedelta(seconds=\
                    (measures[0] / float(TIME_FACTOR)))
            all_measures.append(measures)

        return {self.conso_conf['source']: \
                (self.conso_conf['measures'], all_measures)}




#
# CLI dedicated functions
#

def config_consumption_command(protocol_obj, command, state, \
        **kwargs): #pragma: no cover
    """
    Configure consumption measures.
    Function called when used from command line.
    """

    _ = command
    consumption_kwargs = kwargs
    consumption = None

    if state == 'start':
        consumption = gateway_code.profile.Consumption(**consumption_kwargs)
        # check correct configuration
        if not (consumption.power or consumption.voltage or \
                consumption.current):
            import sys
            print >> sys.stderr, "WARNING:",
            print >> sys.stderr, "No 'power', 'voltage' or 'current' flag set!",
            print >> sys.stderr, "Consumption disabled\n"

    ret = protocol_obj.config_consumption(consumption)
    return ret



def _listen(queue, protocol): #pragma: no cover
    """
    Listen for incoming measures packets.
    Debug function, to be called from Command line.
    """
    import Queue
    while True:
        try:
            raw_pkt = queue.get(True, timeout=1)
            print _str_packet('MEASURE_PKT', raw_pkt)
            measure_pkt = protocol.decode_measure_packet(raw_pkt)
            print measure_pkt
        except Queue.Empty:
            pass

    return 0



def parse_arguments(args): #pragma: no cover
    """
    Parse the arguments, accept following commands
        start, stop, reset_time,
        consumption,
        listen

    """
    import argparse
    parser = argparse.ArgumentParser(prog='protocol')
    sub = parser.add_subparsers(help='commands', dest='command')


    # Start stop commands
    help_alim = 'Alimentation, dc => charging battery'
    parse_start = sub.add_parser('start', help='Start command')
    parse_stop  = sub.add_parser('stop',  help='Stop command')
    parse_start.add_argument('alim', choices=ALIM.keys(), help=help_alim)
    parse_stop.add_argument( 'alim', choices=ALIM.keys(), help=help_alim)

    # Reset time
    _parse_reset  = sub.add_parser('reset_time', help='Reset control node time')

    # Consumption config
    parse_consum = \
            sub.add_parser('consumption', help='Config consumption measures')
    parse_consum.add_argument('state', choices=sorted(INA226_STATE.keys()))
    parse_consum.add_argument('source', choices=sorted(POWER_SOURCE.keys()))
    parse_consum.add_argument('--period', default='2116us', \
            choices=sorted(INA226_PERIOD.keys(), key=(lambda x: int(x[:-2]))), \
            help = 'INA226 measure period')
    parse_consum.add_argument('--average', default='512', \
            choices=sorted(INA226_AVERAGE.keys(), key=int), \
            help = 'INA226 measures average')
    parse_consum.add_argument(\
            '-p', '--power',   help = 'Measure power', action="store_true")
    parse_consum.add_argument(\
            '-v', '--voltage', help = 'Measure voltage', action="store_true")
    parse_consum.add_argument(\
            '-c', '--current', help = 'Measure current', action="store_true")


    # listen to sensor measures
    parse_listen = \
            sub.add_parser('listen', help='listen for measures packets')
    parse_listen.add_argument(\
            'consumption_source', choices=sorted(POWER_SOURCE.keys()))
    parse_listen.add_argument(\
            '-p', '--power',   help = 'Measure power', action="store_true")
    parse_listen.add_argument(\
            '-v', '--voltage', help = 'Measure voltage', action="store_true")
    parse_listen.add_argument(\
            '-c', '--current', help = 'Measure current', action="store_true")





    namespace = parser.parse_args(args)
    print namespace
    return namespace.command, namespace




_ARGS_COMMANDS = {
        'start'       : 'start_stop',
        'stop'        : 'start_stop',
        'reset_time'  : 'reset_time',
        'consumption' : 'config_consumption_command',
        }


def main(args): #pragma: no cover
    """
    Main command line function
    """
    from gateway_code import dispatch, cn_serial_io
    import atexit
    import Queue

    command, arguments = parse_arguments(args[1:])


    measures_queue = Queue.Queue(0)
    dis = dispatch.Dispatch(measures_queue, TYPE_MEASURES_MASK)
    rxtx = cn_serial_io.RxTxSerial(dis.cb_dispatcher)
    dis.io_write = rxtx.write

    rxtx.start()
    atexit.register(rxtx.stop) # execute even if there is an exception


    if command == 'listen':
        try:
            protocol      = Protocol(dis.send_command)
            protocol.time = datetime.now()

            # configure reception for consumption
            measures_flag = 0
            for measure in 'power', 'voltage', 'current':
                if getattr(arguments, measure):
                    measures_flag |= POWER_MEASURES[measure]
            measures_flag |= POWER_SOURCE[arguments.consumption_source]
            protocol.update_consumption_config(measures_flag)

            # configure reception for radio

            ret = _listen(queue = dis.measures_queue, protocol = protocol)

        except KeyboardInterrupt:
            print 'Got Ctrl+C Stopping'
            ret = 0


    else: # simple command
        ret = _ARGS_COMMANDS[command](sender = dis.send_command, \
                **arguments.__dict__)

    print '%s: %r' % (command, ret)



    rxtx.stop()


