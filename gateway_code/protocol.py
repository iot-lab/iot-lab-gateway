"""
Protocol between gateway and control node
"""

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


COMMAND = {'start': OPEN_NODE_START, 'stop': OPEN_NODE_STOP}
ALIM    = {'batt': BATT, 'dc': DC,}




# (res|g)et time
# RESET_OPEN_TIME = chr(0x72)
# GET_OPEN_TIME = chr(0x73)

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



def start_stop(command, alim, dispatcher):

    command_b = COMMAND[command]
    alim_b    = ALIM[alim]

    data = command_b + alim_b

    _print_packet('Sent packet', data)
    result = dispatcher.send_command(data)
    _print_packet('Rec packet', result)





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


    namespace = parser.parse_args(args)
    return namespace.command, namespace



_ARGS_COMMANDS = {
        'start': start_stop,
        'stop':  start_stop,
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




    _ARGS_COMMANDS[command](dispatcher = dis, **arguments.__dict__)

    rxtx.stop()


    # mock queues.put method
    # may be replaced with a regular function for listening
#    oml_queue.put = MagicMock(name='put')
#    dis.queue_control_node.put = MagicMock(name='put')




