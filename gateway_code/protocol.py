"""
Protocol between gateway and control node
"""

import struct
import Queue
import struct

PROTOCOL = {}


# Packet send format
# SYNC_BYTE | LEN | TYPE | -?-?-?-?-

SYNC_BYTE = chr(0x80)
OML_PKT_TYPE = chr(0xF0)


# start stop
OPEN_NODE_START = chr(0x70)
OPEN_NODE_STOP  = chr(0x71)
BATT = chr(0x0)
DC   = chr(0x1)


# (res|g)et time
RESET_OPEN_TIME = chr(0x72)

GET_OPEN_TIME = chr(0x73)
TIME_FACTOR = 32768


ACK  = chr(0x0A)
NACK = chr(0x02)



# MONITOR_POWER = chr(0x42)
# MONITOR_RADIO = chr(0x44)
#
# RADIO_NOISE   = chr(0x45) # ??? 0x4X too ? -> no monitoring values


# CONSUMPTION VALUES

MEASURE_POWER = chr(0xFF)

CONFIG_POWER_POLL   = chr(0x79)

CONSUMPTION_POWER   = 1 << 0
CONSUMPTION_VOLTAGE = 1 << 1
CONSUMPTION_CURRENT = 1 << 2
# nothing on bit 3
CONSUMPTION_3_3V    = 1 << 4
CONSUMPTION_5V      = 1 << 5
CONSUMPTION_BATT    = 1 << 6
# nothing on bit 7
MEASURE_SOURCE = {
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



COMMAND = {'start': OPEN_NODE_START, 'stop': OPEN_NODE_STOP, \
        'reset_time': RESET_OPEN_TIME, 'get_time': GET_OPEN_TIME, \
        'consumption': CONFIG_POWER_POLL}
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

def send_cmd(dispatcher, data):

    _print_packet('Sent packet', data)
    result = dispatcher.send_command(data)
    _print_packet('Rec packet', result)

    return result




def start_stop(dispatcher, command, alim):

    command_b = COMMAND[command]
    alim_b    = ALIM[alim]

    data = command_b + alim_b

    result = send_cmd(dispatcher, data)

    # only type and ACK
    ret = _valid_result_command(result, command_b, 2)
    return ret


def reset_time(dispatcher, command):

    command_b = COMMAND[command]
    data = command_b

    result = send_cmd(dispatcher, data)

    # only type and ACK
    ret = _valid_result_command(result, command_b, 2)
    return ret


def get_time(dispatcher, command):
    command_b = COMMAND[command]
    data = command_b

    result = send_cmd(dispatcher, data)

    # type, ACK, and an unsigned long (4bytes)
    ret = _valid_result_command(result, command_b, 6)
    if not ret:
        raise ValueError

    data_result = result[2:]
    control_time_tick = struct.unpack('!L', data_result)[0]
    control_time_seconds = control_time_tick / float(TIME_FACTOR)

    return control_time_seconds



def config_consumption(dispatcher, command, source, period, average, status):

    meas_aux = CONSUMPTION_POWER | CONSUMPTION_VOLTAGE | CONSUMPTION_CURRENT

    command_b = COMMAND[command]

    source_b  = chr(meas_aux | MEASURE_SOURCE[source])
    config_b = chr(period | average << 4 | INA226_STATUS[status])

    data = command_b + source_b + config_b

    result = send_cmd(dispatcher, data)

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
    measures_list = ['t'] + \
            (['p'] if conf & CONSUMPTION_POWER else []) + \
            (['v'] if conf & CONSUMPTION_VOLTAGE else []) + \
            (['c'] if conf & CONSUMPTION_CURRENT else [])
    unpack_str = '!L' + ('f' * (len(measures_list) - 1))
    measures_len = 4 + 4 * (len(measures_list) -1) # 4 bytes for time + 4bytes per value (float)
    CONSUMPTION_DECODE_VALUES[conf] = (measures_list, unpack_str, measures_len)

CONSUMPTION_SOURCE_VALUES = dict([(MEASURE_SOURCE[key], key) \
        for key in MEASURE_SOURCE])


def decode_consumption_packet(pkt):

    header_size = 3
    unpack_str = '!'
    config = ord(pkt[1])
    count  = ord(pkt[2])

    values, unpack_str, measures_len = CONSUMPTION_DECODE_VALUES[config & 0x7]
    num_values = len(values)
    power_source = CONSUMPTION_SOURCE_VALUES[config & 0x70]

    chunks = [pkt[start:start + num_values * measures_len] for start in range(header_size, len(pkt), num_values * measures_len)]
    assert len(chunks) == count

    all_measures = []
    for raw_measure in chunks:
        measures = list(struct.unpack(unpack_str, raw_measure))
        # convert time to float
        measures[0] = measures[0] / float(TIME_FACTOR)
        all_measures.append(measures)

    return {power_source: (values, all_measures)}




MEASURES_DECODE = {
        MEASURE_POWER: decode_consumption_packet,
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

def listen(dispatcher, command):
    oml_queue = dispatcher.queue_oml

    while True:
        try:
            pkt = oml_queue.get(True, timeout=1)
            _print_packet('MEASURE_PKT', pkt)
            decode_measure_packet(pkt)
        except Queue.Empty:
            pass
        except KeyboardInterrupt:
            break

    return 0




def parse_arguments(args):
    import argparse
    parser = argparse.ArgumentParser(prog='protocol')
    sub = parser.add_subparsers(help='commands', dest='command')


    parse_start = sub.add_parser('start', help='Start command')
    parse_start.add_argument('alim', choices=['dc', 'batt'], \
            help='Alimentation, dc => charging battery')

    parse_stop  = sub.add_parser('stop', help='Stop command')
    parse_stop.add_argument('alim', choices=['dc', 'batt'], \
            help='Alimentation, dc => charging battery')

    _parse_reset  = sub.add_parser('reset_time', help='Reset control node time')

    _parse_get  = sub.add_parser('get_time', help='Get control node time')

    # polling
    parse_consumption  = sub.add_parser('consumption', \
            help='Reset control node time')
    parse_consumption.add_argument('status', choices=['start', 'stop'])
    parse_consumption.add_argument('source', choices=['3.3V', '5V', 'BATT'])
    parse_consumption.add_argument('-p', '--period', type=int, choices=range(0, 8), \
            default=4, help = 'See definition in the code')
    parse_consumption.add_argument('-a', '--average', type=int, choices=range(0, 8), \
            default=5, help = 'See definition in the code')

    _parse_listen_measures = sub.add_parser('listen', \
            help='listen for measures packets')


    namespace = parser.parse_args(args)
    print namespace
    return namespace.command, namespace


_ARGS_COMMANDS = {
        'start': start_stop,
        'stop':  start_stop,
        'reset_time': reset_time,
        'get_time': get_time,
        'consumption':config_consumption,
        'listen': listen,
        }




def main(args):
    from gateway_code import dispatch, cn_serial_io
    command, arguments = parse_arguments(args[1:])


    oml_queue = Queue.Queue(0)
    dis = dispatch.Dispatch(oml_queue, OML_PKT_TYPE)
    rxtx = cn_serial_io.RxTxSerial(dis.cb_dispatcher)
    dis.io_write = rxtx.write


    rxtx.start()

    try:
        ret = _ARGS_COMMANDS[command](dispatcher = dis, **arguments.__dict__)
        print '%s: %r' % (command, ret)
    except:
        import sys
        print 'Exception'
        print sys.exc_info()[0]


    rxtx.stop()


