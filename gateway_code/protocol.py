"""
Protocol between gateway and control node
"""

import struct
import Queue
import gateway_code.profile

PROTOCOL = {}


# Packet send format
# SYNC_BYTE | LEN | TYPE | -?-?-?-?-
SYNC_BYTE = chr(0x80)



#
# TYPE of packets
#

# Commands
# start stop
TYPE_CMD_OPEN_NODE_START = chr(0x70)
TYPE_CMD_OPEN_NODE_STOP  = chr(0x71)
# reset time
TYPE_CMD_RESET_TIME = chr(0x72)
# Config RADIO
# TYPE_CMD_CONFIG_RADIO =

# Radio Noise
# TYPE_CMD_CONFIG_RADIO_NOISE = ? -> no monitoring values
# fake sensor
# TYPE_CMD_CONFIG_FAKE_SENSOR = ?

# Config measures
TYPE_CMD_CONFIG_MEASURES_CONSUMPTION = chr(0x79)
# TYPE_CMD_CONFIG_MEASURES_RADIO = ?
# TYPE_CMD_CONFIG_MEASURES_SNIFFER = ?





BATT = chr(0x0)
DC   = chr(0x1)

TIME_FACTOR = 32768

ACK  = chr(0x0A)
NACK = chr(0x02)


#
# Measures packets
#

# Config
# SYNC_BYTE | LEN | TYPE | MEASURE_SOURCES | MEASURE_CONFIG
# Measures values
# SYNC_BYTE | LEN | TYPE | MEASURE_SOURCES | Measures_count | [TIME | Values ]*|

TYPE_MEASURES_MASK = 0xF0

# Consumption measures

TYPE_MEASURES_CONSUMPTION = chr(0xFF)

# Measures sources flags
# may be the 3 following
CONSUMPTION_POWER   = 1 << 0
CONSUMPTION_VOLTAGE = 1 << 1
CONSUMPTION_CURRENT = 1 << 2

POWER_MEASURES = {
        'power': CONSUMPTION_POWER,
        'voltage': CONSUMPTION_VOLTAGE,
        'current': CONSUMPTION_CURRENT,
        }

# nothing on bit 3
# Only one of the following
CONSUMPTION_3_3V    = 1 << 4
CONSUMPTION_5V      = 1 << 5
CONSUMPTION_BATT    = 1 << 6
# nothing on bit 7

POWER_SOURCE = {
        '3.3V' : CONSUMPTION_3_3V,
        '5V'   : CONSUMPTION_5V,
        'BATT' : CONSUMPTION_BATT,
        }


# CONFIG BYTE == [ PERIOD | AVERAGE << 4 | ENABLE(BIT7) ]

# Period
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

# Average
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

# ENABLE/DISABLE
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


def _print_packet(info, data):
    """
    Debug function that prints a packet
    """
    import sys
    debug_out = info + ": '"
    if data is None:
        debug_out += str(None)
    else:
        for i in data:
            debug_out += '%02X ' % ord(i)

    debug_out += "'"
    print >> sys.stderr, debug_out

def _valid_result_command(packet, pkt_type, length):
    """
    Validate type of packet,
    ACK/NACK
    and length
    """

    if packet is None:
        return False
    ret = True
    ret &= (packet[0] == pkt_type)
    ret &= (packet[1] == ACK)
    ret &= (len(packet) == length)

    return ret

def send_cmd(sender, data):
    """
    Send a command to the control node and wait for it's answer.
    """

    _print_packet('Sent packet', data)
    result = sender(data)
    _print_packet('Rec packet', result)

    return result




def start_stop(sender, command, alim):
    """
    Start or stop open node via the control node and use given alim.
    """

    command_b = COMMAND[command]
    alim_b    = ALIM[alim]
    data      = command_b + alim_b

    result = send_cmd(sender, data)

    ret = _valid_result_command(result, command_b, 2) # type and [N]ACK
    return ret


def reset_time(sender, command):
    """
    Reset the time reference on the control node at 0
    """

    command_b = COMMAND[command]
    data      = command_b

    result = send_cmd(sender, data)

    ret = _valid_result_command(result, command_b, 2) # type and [N]ACK
    return ret


def config_consumption_command(sender, command, state, **kwargs):
    """
    Configure consumption measures.
    Function called when used from command line.
    """

    _ = command
    consumption_kwargs = kwargs
    consumption = None

    if state == 'start':
        consumption = gateway_code.profile.Consumption(**consumption_kwargs)

    ret = config_consumption(sender, consumption)
    return ret


def config_consumption(sender, consumption=None):
    """
    Configure consumption measures

    :param sender: function that sends command
    :param consumption: the consumption object
    :type consumption: gateway_code.profile.Consumption
    """

    command_b     = COMMAND['consumption']
    measures_flag = 0
    config_flag   = 0

    if consumption is not None:
        # start and configure consumption
        measures_flag |= POWER_MEASURES['power']   if consumption.power   else 0
        measures_flag |= POWER_MEASURES['voltage'] if consumption.voltage else 0
        measures_flag |= POWER_MEASURES['current'] if consumption.current else 0
        measures_flag |= POWER_SOURCE[consumption.source]

        config_flag |= INA226_PERIOD[consumption.period]
        config_flag |= INA226_AVERAGE[consumption.average] << 4
        config_flag |= INA226_STATE['start']

    else:
        # stop consumption measures
        config_flag |= INA226_STATE['stop']


    data = command_b + chr(measures_flag) + chr(config_flag)
    result = send_cmd(sender, data)

    ret = _valid_result_command(result, command_b, 2) # type and [N]ACK
    return ret




CONSUMPTION_TUPLE = \
        ((CONSUMPTION_POWER, 'p'), \
        (CONSUMPTION_VOLTAGE, 'v'), \
        (CONSUMPTION_CURRENT, 'c'))


# store list of measures and associated unpack strings for each config
CONSUMPTION_DECODE_VALUES = {}
for conf in range(1, 1 << 3):
    _measures_list = ['t'] + \
            (['p'] if conf & CONSUMPTION_POWER else []) + \
            (['v'] if conf & CONSUMPTION_VOLTAGE else []) + \
            (['c'] if conf & CONSUMPTION_CURRENT else [])
    _unpack_str = '!L' + ('f' * (len(_measures_list) - 1))
    # 4 bytes for time + 4bytes per value (float)
    _measures_len = 4 + 4 * (len(_measures_list) -1)
    CONSUMPTION_DECODE_VALUES[conf] = \
            (_measures_list, _unpack_str, _measures_len)

CONSUMPTION_SOURCE_VALUES = dict([(POWER_SOURCE[key], key) \
        for key in POWER_SOURCE])


def decode_consumption_pkt(pkt):
    """
    Extract measures stored in pkt.
    """

    header_size = 3
    unpack_str  = '!'
    config = ord(pkt[1])
    count  = ord(pkt[2])

    # decode current frame content
    power_source                      = CONSUMPTION_SOURCE_VALUES[config & 0x70]
    values, unpack_str, measures_size = CONSUMPTION_DECODE_VALUES[config & 0x7]

    assert len(pkt) == header_size + count * measures_size
    # extract list of raw measures from payload
    chunks = [pkt[start:start + measures_size] for start in \
            range(header_size, len(pkt), measures_size)]
    assert len(chunks) == count

    # extract the 'count' measures
    all_measures = []
    for raw_measure in chunks:
        measures = list(struct.unpack(unpack_str, raw_measure))
        measures[0] = measures[0] / float(TIME_FACTOR) # convert tick to seconds
        all_measures.append(measures)

    return {power_source: (values, all_measures)}




MEASURES_DECODE = {
        TYPE_MEASURES_CONSUMPTION: decode_consumption_pkt,
        }

def decode_measure_packet(pkt):
    """
    Generic measure decoding function.
    Calls the appropriate function for each type.
    """
    fct = MEASURES_DECODE.get(pkt[0], None)

    if fct is None:
        import sys
        print >> sys.stderr, 'Uknown measure packet: %02X' % ord(pkt[0])
    else:
        print fct(pkt)

def _listen(queue, command):
    """
    Listen for incoming measures packets.
    Debug function, to be called from Command line.
    """
    _ = command

    while True:
        try:
            pkt = queue.get(True, timeout=1)
            _print_packet('MEASURE_PKT', pkt)
            decode_measure_packet(pkt)
        except Queue.Empty:
            pass
        except KeyboardInterrupt:
            break

    return 0




def parse_arguments(args):
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
    _parse_listen_measures = \
            sub.add_parser('listen', help='listen for measures packets')

    namespace = parser.parse_args(args)
    print namespace
    return namespace.command, namespace


_ARGS_COMMANDS = {
        'start': start_stop,
        'stop':  start_stop,
        'reset_time': reset_time,
        'consumption':config_consumption_command,
        'listen': _listen,
        }


def main(args):
    """
    Main command line function
    """
    from gateway_code import dispatch, cn_serial_io
    import atexit

    command, arguments = parse_arguments(args[1:])


    measures_queue = Queue.Queue(0)
    dis = dispatch.Dispatch(measures_queue, TYPE_MEASURES_MASK)
    rxtx = cn_serial_io.RxTxSerial(dis.cb_dispatcher)
    dis.io_write = rxtx.write


    rxtx.start()
    atexit.register(rxtx.stop) # execute even if there is an exception


    if command == 'listen':
        ret = _ARGS_COMMANDS[command](queue = dis.measures_queue, \
                **arguments.__dict__)
        print '%s: %r' % (command, ret)

    else: # simple command
        ret = _ARGS_COMMANDS[command](sender = dis.send_command, \
                **arguments.__dict__)
        print '%s: %r' % (command, ret)




    rxtx.stop()


