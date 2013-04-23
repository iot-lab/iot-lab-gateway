"""
Protocol between gateway and control node
"""

import struct
import Queue

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
# nothing on bit 3
# Only one of the following
CONSUMPTION_3_3V    = 1 << 4
CONSUMPTION_5V      = 1 << 5
CONSUMPTION_BATT    = 1 << 6
# nothing on bit 7

MEASURE_POWER_SOURCE = {
        '3.3V':CONSUMPTION_3_3V,
        '5V':CONSUMPTION_5V,
        'BATT':CONSUMPTION_BATT,
        }


# CONFIG BYTE == [ PERIOD | AVERAGE << 4 | ENABLE(BIT7) ]

# Period
INA226_PERIOD_140US  = 0
INA226_PERIOD_204US  = 1
INA226_PERIOD_332US  = 2
INA226_PERIOD_588US  = 3
INA226_PERIOD_1100US = 4
INA226_PERIOD_2116US = 5
INA226_PERIOD_4156US = 6
INA226_PERIOD_8244US = 7

# Average
INA226_AVERAGE_1     = 0
INA226_AVERAGE_4     = 1
INA226_AVERAGE_16    = 2
INA226_AVERAGE_64    = 3
INA226_AVERAGE_128   = 4
INA226_AVERAGE_256   = 5
INA226_AVERAGE_512   = 6
INA226_AVERAGE_1024  = 7
# ENABLE/DISABLE
INA226_ENABLE        = 1 << 7
INA226_DISABLE       = 0 << 7

INA226_STATUS = {
        'start': INA226_ENABLE,
        'stop': INA226_DISABLE,
        }



COMMAND = {'start': TYPE_CMD_OPEN_NODE_START, 'stop': TYPE_CMD_OPEN_NODE_STOP, \
        'reset_time': TYPE_CMD_RESET_TIME, \
        'consumption': TYPE_CMD_CONFIG_MEASURES_CONSUMPTION}
ALIM    = {'batt': BATT, 'dc': DC,}


def _print_packet(info, data):
    debug_out = info + ": '"
    if data is None:
        debug_out += str(None)
    else:
        for i in data:
            debug_out += '%02X ' % ord(i)

    debug_out += "'"
    print debug_out

def _valid_result_command(packet, pkt_type, length):
    """
    Validate type of packet,
    ACK/NACK
    and length
    """

    if packet is None:
        return False
    ret = True
    ret &= packet[0] == pkt_type
    ret &= packet[1] == ACK
    ret &= len(packet) == length

    return ret

def send_cmd(sender, data):

    _print_packet('Sent packet', data)
    result = sender(data)
    _print_packet('Rec packet', result)

    return result




def start_stop(sender, command, alim):

    command_b = COMMAND[command]
    alim_b    = ALIM[alim]

    data = command_b + alim_b

    result = send_cmd(sender, data)

    # only type and ACK
    ret = _valid_result_command(result, command_b, 2)
    return ret


def reset_time(sender, command):

    command_b = COMMAND[command]
    data = command_b

    result = send_cmd(sender, data)

    # only type and ACK
    ret = _valid_result_command(result, command_b, 2)
    return ret



def config_consumption(sender, command, source, period, average, status):

    meas_values = CONSUMPTION_POWER | CONSUMPTION_VOLTAGE | CONSUMPTION_CURRENT

    command_b = COMMAND[command]

    source_b  = chr(meas_values | MEASURE_POWER_SOURCE[source])
    config_b = chr(period | average << 4 | INA226_STATUS[status])

    data = command_b + source_b + config_b

    result = send_cmd(sender, data)

    # only type and ACK
    ret = _valid_result_command(result, command_b, 2)
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

CONSUMPTION_SOURCE_VALUES = dict([(MEASURE_POWER_SOURCE[key], key) \
        for key in MEASURE_POWER_SOURCE])


def decode_consumption_pkt(pkt):

    header_size = 3
    unpack_str = '!'
    config = ord(pkt[1])
    count  = ord(pkt[2])

    values, unpack_str, measures_len = CONSUMPTION_DECODE_VALUES[config & 0x7]
    num_values = len(values)
    power_source = CONSUMPTION_SOURCE_VALUES[config & 0x70]

    chunks = [pkt[start:start + num_values * measures_len] for start in \
            range(header_size, len(pkt), num_values * measures_len)]
    assert len(chunks) == count

    all_measures = []
    for raw_measure in chunks:
        measures = list(struct.unpack(unpack_str, raw_measure))
        # convert time to float
        measures[0] = measures[0] / float(TIME_FACTOR)
        all_measures.append(measures)

    return {power_source: (values, all_measures)}




MEASURES_DECODE = {
        TYPE_MEASURES_CONSUMPTION: decode_consumption_pkt,
        }

def decode_measure_packet(pkt):
    # ret = _valid_result_command(pkt, command_b, 2)
    #   FF 17 01 4B BD A3 8E 3E 07 52 82 40 4F 0A 3D 3D 27 57 95
    fct = MEASURES_DECODE.get(pkt[0], None)

    if fct is None:
        import sys
        print >> sys.stderr, 'Uknown measure packet: %02X' % ord(pkt[0])
    else:
        print fct(pkt)

def listen(queue, _command):

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
    parse_start.add_argument('alim', choices=['dc', 'batt'], help=help_alim)
    parse_stop  = sub.add_parser('stop', help='Stop command')
    parse_stop.add_argument('alim', choices=['dc', 'batt'], help=help_alim)

    # Reset time
    _parse_reset  = sub.add_parser('reset_time', help='Reset control node time')

    # Consumption config
    parse_consumption = sub.add_parser('consumption', \
            help='Config consumption measures')
    parse_consumption.add_argument('status', choices=['start', 'stop'])
    parse_consumption.add_argument('source', choices=['3.3V', '5V', 'BATT'])
    parse_consumption.add_argument('-p', '--period', type=int, \
            choices=range(0, 8), default=4, help = 'See definition in the code')
    parse_consumption.add_argument('-a', '--average', type=int, \
            choices=range(0, 8), default=5, help = 'See definition in the code')

    # listen to sensor measures
    _parse_listen_measures = sub.add_parser('listen', \
            help='listen for measures packets')

    namespace = parser.parse_args(args)
    return namespace.command, namespace


_ARGS_COMMANDS = {
        'start': start_stop,
        'stop':  start_stop,
        'reset_time': reset_time,
        'consumption':config_consumption,
        'listen': listen,
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


