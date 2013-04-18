"""
Protocol between gateway and control node
"""

PROTOCOL = {}


# Packet send format
# SYNC_BYTE | LEN | TYPE | -?-?-?-?-

SYNC_BYTE = chr(0x80)


# Start stop commands
OPEN_START_DC_AND_CHARGE = 0
OPEN_START_BATT          = 0

OPEN_STOP_CHARGE         = 0
OPEN_STOP_NO_CHARGE      = 0

# or start + config ?

MONITOR_POWER = chr(0x42)
MONITOR_RADIO = chr(0x44)

RADIO_NOISE   = chr(0x45) # ??? 0x4X too ? -> no monitoring values


# start stop
OPEN_NODE_START = chr(0x70)
OPEN_NODE_STOP  = chr(0x71)

# (res|g)et time
RESET_OPEN_TIME = chr(0x72)
GET_OPEN_TIME = chr(0x73)


# Consumption byte configuration

CONSUMPTION_POWER   = 0
CONSUMPTION_VOLTAGE = 1 << 0
CONSUMPTION_CURRENT = 1 << 1
# nothing on bit 3
CONSUMPTION_3_3V    = 1 << 3
CONSUMPTION_5V      = 1 << 4
CONSUMPTION_BATT    = 1 << 5
# bit 7
CONSUMPTION_ENABLE  = 1 << 6
CONSUMPTION_DISABLE = 0









def main(args):
    pass

