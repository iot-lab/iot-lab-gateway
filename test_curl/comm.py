
"""
This script run on the gateway, send command to the control node and
receive 1 acknowledge frame per command and in option in case of
polling command, polling frame.
main.c from appli/iotlab/control_node/ is the control node SW
"""

import serial
import sys
import time
import struct
import pdb
import threading

SYNC_BYTE = chr(0x80)
OPENNODE_START = chr(0x15)
OPENNODE_STARTBATTERY = chr(0x16)
OPENNODE_STOP = chr(0x17)
CONFIG_RADIO = chr(0x40)
CONFIG_POWERPOLL = chr(0x42)
CONFIG_RADIOPOLL = chr(0x44)
CONFIG_RADIONOISE = chr(0x45)
SET_TIME = chr(0x52)
FAKE_SIMPLE_POLLING = chr(0x60)

ser = serial.Serial('/dev/ttyFITECO_GWT', 500000, timeout=16)
Running=True

def readFrame():
    global Running
    while Running==True :
        byte = ser.read(1)
        if len(byte) == 1:
            sync = struct.unpack("<c", byte)
            print hex(ord(byte)), sync

t = threading.Thread(None, readFrame, None, (), {})
t.start()

print "OPENNODE_START"
ser.write(SYNC_BYTE)
ser.write(chr(0x2))
ser.write(OPENNODE_START)
ser.write('\x01')
#tempo to have serial data to be received before next print
time.sleep(1)

print "OPENNODE_STARTBATTERY"
ser.write(SYNC_BYTE)
ser.write(chr(0x2))
ser.write(OPENNODE_STARTBATTERY)
ser.write('\x01')
#tempo to have serial data to be received before next print
time.sleep(1)

print "OPENNODE_STOP"
ser.write(SYNC_BYTE)
ser.write(chr(0x2))
ser.write(OPENNODE_STOP)
ser.write('\x01')
#tempo to have serial data to be received before next print
time.sleep(1)

print "CONFIG_RADIO"
ser.write(SYNC_BYTE)
ser.write(chr(0x2))
ser.write(CONFIG_RADIO)
ser.write('\x01')
#tempo to have serial data to be received before next print
time.sleep(1)

print "CONFIG_POWERPOLL"
ser.write(SYNC_BYTE)
ser.write(chr(0x2))
ser.write(CONFIG_POWERPOLL)
ser.write('\x01')
#tempo to have serial data to be received before next print
time.sleep(1)

print "CONFIG_RADIOPOLL"
ser.write(SYNC_BYTE)
ser.write(chr(0x2))
ser.write(CONFIG_RADIOPOLL)
ser.write('\x01')
#tempo to have serial data to be received before next print
time.sleep(1)

print "CONFIG_RADIONOISE" 
ser.write(SYNC_BYTE)
ser.write(chr(0x2))
ser.write(CONFIG_RADIONOISE)
ser.write('\x01')
#tempo to have serial data to be received before next print
time.sleep(1)

print "stop FAKE_SIMPLE_POLLING"
ser.write(SYNC_BYTE)
ser.write(chr(0x2))
ser.write(FAKE_SIMPLE_POLLING)
ser.write('\x00')
time.sleep(1)

print "start FAKE_SIMPLE_POLLING"
ser.write(SYNC_BYTE)
ser.write(chr(0x2))
ser.write(FAKE_SIMPLE_POLLING)
ser.write('\x01')

#also this tempo is used to give time to some polling
time.sleep(1)

print "stop FAKE_SIMPLE_POLLING"
ser.write(SYNC_BYTE)
ser.write(chr(0x2))
ser.write(FAKE_SIMPLE_POLLING)
ser.write('\x00')
#ser.write(chr(0xd)) # useful only to see something in miniterm.py
#ser.write(chr(0xa))
time.sleep(1)

#stop the reading thread
Running=False
time.sleep(1)

sys.exit(0)


"""
  def readCmd(self):

   self.Running=True

   data = ''

  while self.Running==True:
             data += ser.read(1024)

             if '\r\n' in data:
                 end_ix = data.inde'\r\n')+2
                 line = data[:end_ix]
                 data = data[end_ix:]
                #print "RAW LINE=",line

                sync = struct.unpack("=h", data[0])
                cmd = struct.unpack("=h", data[1])
                param = struct.unpack("=hh", data[2:4])
"""
