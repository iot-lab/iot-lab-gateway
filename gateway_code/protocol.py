"""
Protocol between gateway and control node
"""

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


COMMAND = {'start': OPEN_NODE_START, 'stop': OPEN_NODE_STOP, \
        'reset_time': RESET_OPEN_TIME, 'get_time': GET_OPEN_TIME}
ALIM    = {'batt': BATT, 'dc': DC,}



# MONITOR_POWER = chr(0x42)
# MONITOR_RADIO = chr(0x44)
#
# RADIO_NOISE   = chr(0x45) # ??? 0x4X too ? -> no monitoring values


# Consumption byte configuration

#  CONSUMPTION_POWER   = 0
#  CONSUMPTION_VOLTAGE = 1 << 0
#  CONSUMPTION_CURRENT = 1 << 1
#  # nothing on bit 3
#  CONSUMPTION_3_3V    = 1 << 3
#  CONSUMPTION_5V      = 1 << 4
#  CONSUMPTION_BATT    = 1 << 5
#  # bit 7
#  CONSUMPTION_ENABLE  = 1 << 6
#  CONSUMPTION_DISABLE = 0


def _print_packet(info, data):
    debug_out = info + ": '"
    for i in data:
        debug_out += '%02X' % ord(i)
    debug_out += "'"
    print debug_out

def _valid_result_command(packet, type, length):
    """
    Validate type of packet,
    ACK/NACK
    and length
    """

    ret = True
    ret &= packet[0] == type
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

    parse_reset  = sub.add_parser('reset_time', help='Reset control node time')

    parse_get  = sub.add_parser('get_time', help='Get control node time')


    namespace = parser.parse_args(args)
    return namespace.command, namespace



_ARGS_COMMANDS = {
        'start': start_stop,
        'stop':  start_stop,
        'reset_time': reset_time,
        'get_time': get_time,
        }



def main(args):
    from gateway_code import dispatch, cn_serial_io
    import Queue
    command, arguments = parse_arguments(args[1:])


    oml_queue = Queue.Queue(0)
    dis = dispatch.Dispatch(oml_queue, OML_PKT_TYPE)
    rxtx = cn_serial_io.RxTxSerial(dis.cb_dispatcher)
    dis.io_write = rxtx.write


    rxtx.start()




    ret = _ARGS_COMMANDS[command](dispatcher = dis, **arguments.__dict__)
    print '%s: %r' % (command, ret)

    rxtx.stop()


    # mock queues.put method
    # may be replaced with a regular function for listening
#    oml_queue.put = MagicMock(name='put')
#    dis.queue_control_node.put = MagicMock(name='put')




