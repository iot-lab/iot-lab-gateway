#---------------------------------------------------------------------------
# Tools for sniffer
#
# Cedric Adjih, Inria, 2012-2014
#---------------------------------------------------------------------------

import sys, time, struct, select, socket, fcntl, os
import argparse, hashlib, subprocess

#---------------------------------------------------------------------------
# An Observer/Parser that receives data under SNIF format, parse it,
# output them to another Observer/Output
#---------------------------------------------------------------------------

Foren6FieldFlags = {
    "crc":        1,
    "crcOk":      2,
    "rssi":       4,
    "lqi":        8,
    "timestamp": 16
    }


class Foren6SnifferParser:
    def __init__(self, snifferId, observer):
        self.data = ""
        self.state = "init"
        self.snifferId = snifferId
        self.observer = observer

    HeaderSpec = "4sBB"
    FieldFlags = Foren6FieldFlags # XXX

    def notifyData(self, data):
        if len(data) == 0:
            warnings.warn("empty data in Foren6 Sniffer Parser")
            return
        self.data += data
        while True:
            if self.state == "init":
                self.handleInputInit()
                if self.state == "init":
                    break
            elif (self.state == "header" 
                  and len(self.data) >= struct.calcsize(self.HeaderSpec)):
                self.handleInputHeader()
            elif (self.state == "packet" 
                  and len(self.data) 
                  >= self.header["size"]+self.header["infoSize"]):
                self.handleInputPacket()
            else: break

    def handleInputInit(self):
        assert self.state == "init"
        pos = self.data.find("SNIF")
        if pos != 0 and pos !=-1:
            print "[Foren6SnifferParser.handleInputInit: pos=%s]" % pos
        if pos < 0:
            return
        self.data = self.data[pos:]
        self.state = "header"
        self.clock = time.time()
        
    def handleInputHeader(self):
        assert self.state == "header"
        headerSize = struct.calcsize(self.HeaderSpec)
        (magic, pktType, pktSize
         ) = struct.unpack(self.HeaderSpec, self.data[:headerSize])
        

        self.header = {"magic": magic, "type": pktType, "size": pktSize,
                       "infoSize": self.getInfoSize(pktType) }
        self.data = self.data[headerSize:]
        self.state = "packet"

    def getInfoSize(self, flags):
        result = 0
        for name, spec in [("crc", "H"), ("crcOk", "B"), ("rssi","B"),
                           ("lqi", "B"), ("timestamp","B")]:
            if (self.FieldFlags[name] & flags) != 0:
                result += struct.calcsize(spec)
        return result
        
    def handleInputPacket(self):
        assert self.state == "packet"
        pktType = self.header["type"]
        pktSize = self.header["size"]
        pktData, self.data = self.data[:pktSize], self.data[pktSize:]
        if (self.FieldFlags["crc"] & pktType) != 0:
            (crc,),self.data = popStruct("H", self.data)
        else: crc = 0
        if (self.FieldFlags["crcOk"] & pktType) != 0:
            (crcOk,),self.data = popStruct("B", self.data)
        else: crcOk = 0
        if (self.FieldFlags["rssi"] & pktType) != 0:
            (rssi,),self.data = popStruct("B", self.data)
        else: rssi = 0
        if (self.FieldFlags["lqi"] & pktType) != 0:
            (lqi,),self.data = popStruct("B", self.data)
        else: lqi = 0
        if (self.FieldFlags["timestamp"] & pktType) != 0:
            (timestamp,),self.data = popStruct("B", self.data)
        else: timestamp = 0

        channel = 10

        info = self.header.copy()
        info["clock"]     = self.clock
        info["crc"]       = crc
        info["crcOk"]     = crcOk
        info["rssi"]      = rssi
        info["lqi"]       = lqi
        info["timestamp"] = timestamp
        info["snifferId"] = self.snifferId
        info["channel"]   = channel
        info["packet"]    = pktData
        
        if self.observer != None:
            self.observer.notifyPacket(info)

        self.state = "init"
        self.header = None
        self.clock = None

#---------------------------------------------------------------------------
# Raw recording of data
#---------------------------------------------------------------------------

def openSocket(i):
    global socketOf, indexOfSocket
    sd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sd.connect(("localhost", 3000+i))
    socketOf[i] = sd
    indexOfSocket[sd] = i
    fcntl.fcntl(sd, fcntl.F_SETFL, os.O_NONBLOCK)

#---------------------------------------------------------------------------
#
#---------------------------------------------------------------------------

if False:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nb-sniffers", type=int, default=None)
    parser.add_argument("--record", dest="fileName", default=None)
    args = parser.parse_args()


    nbSniffers = args.nb_sniffers
    outputFileName = args.fileName

    refTime = time.time()

    f = open(outputFileName, "w")

    socketOf = {}
    indexOfSocket = {}

    for i in range(nbSniffers):
        openSocket(i)

    while True:
        socketList = list(socketOf.values())
        rList, unused, unused = select.select(socketList, [], [])
        sys.stdout.write(".")
        sys.stdout.flush()
        for sd in rList:
            snifferId = indexOfSocket[sd]
            clock = time.time() - refTime
            data = sd.recv(8192)
            if len(data) == 0:
                sd.close()
                del indexOfSocket[sd]
                sys.stdout.write("*")
                sys.stdout.flush()
                openSocket(snifferId)
            header = struct.pack("!fBH", clock, snifferId, len(data))
            f.write(header+data)
            f.flush()

#---------------------------------------------------------------------------
# Send a recorded "SNIF" file to wireshark through ZEP on localhost
#---------------------------------------------------------------------------

# * Packet type: sniffed packet
# * Format:  magic | type | len | pkt | crc_ok | rssi | lqi

HeaderSpec = "4sBB"

FieldFlags = {
    "crc":        1,
    "crcOk":      2,
    "rssi":       4,
    "lqi":        8,
    "timestamp": 16
    }

def popStruct(spec, data):
    specSize = struct.calcsize(spec)
    result = struct.unpack(spec, data[:specSize])
    return result, data[specSize:]
    
def sendSnifToZep(fileName):
    f = open(fileName)
    data = f.read()
    f.close()

    toWireshark = WiresharkSender() 

    while len(data) > 0:
        pos = data.find("SNIF")
        if pos < 0:
            break
        data = data[pos:]
        headerSize = struct.calcsize(HeaderSpec)
        (magic, pktType, pktSize) = struct.unpack(HeaderSpec, data[:headerSize])
        data = data[headerSize:]
        pktData, data = data[:pktSize], data[pktSize:]
        if (FieldFlags["crc"] & pktType) != 0:
            (crc,),data = popStruct("H", data)
        else: crc = 0
        if (FieldFlags["crcOk"] & pktType) != 0:
            (crcOk,),data = popStruct("B", data)
        else: crcOk = 0
        if (FieldFlags["rssi"] & pktType) != 0:
            (rssi,),data = popStruct("B", data)
        else: rssi = 0
        if (FieldFlags["lqi"] & pktType) != 0:
            (lqi,),data = popStruct("B", data)
        else: lqi = 0
        if (FieldFlags["timestamp"] & pktType) != 0:
            (timestamp,),data = popStruct("B", data)
        else: timestamp = 0

        print magic, pktType, pktSize, pos,
        print "->", crcOk, rssi, lqi, timestamp

        snifferId = 1
        channel = 10
        toWireshark.sendAsZep((timestamp, snifferId, pktData, channel, rssi))

#---------------------------------------------------------------------------
# [CA] Copied from contiki-senslab-unified/tools/cooja/jython/PySimul.py
# (I wrote in 2012-2013)
#---------------------------------------------------------------------------

import struct, socket

# From packet-zep.c in wireshark:
# ZEP v2 Header will have the following format (if type=1/Data):
# |Preamble|Version| Type |Channel ID|Device ID|CRC/LQI Mode|LQI Val|NTP Timestamp|Sequence#|Reserved|Length|
# |2 bytes |1 byte |1 byte|  1 byte  | 2 bytes |   1 byte   |1 byte |   8 bytes   | 4 bytes |10 bytes|1 byte|
#ZepHeader = struct.pack("BBB", ord('E'), ord('X'), 2) # Preamble + Version
#^^^^ is an unicode string in Jython
ZepPort = 17754 

#--------------------------------------------------

# http://stackoverflow.com/questions/8244204/ntp-timestamps-in-python
#import datetime
#SYSTEM_EPOCH = datetime.date(*_time.gmtime(0)[0:3])
#NTP_EPOCH = datetime.date(1900, 1, 1)
#NTP_DELTA = (SYSTEM_EPOCH - NTP_EPOCH).days * 24 * 3600

NTP_DELTA = float(2208988800L) # XXX: fix NTP timestamp handling

#--------------------------------------------------

class ZepSender:
    def __init__(self, refTime = 0):
        self.sd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sd.bind(("", ZepPort))
        self.counter = 0
        self.notified = False
        self.refClock = (int(refTime)//(60*60*24))*(60*60*24)-60*60

    def sendAsZep(self, packetInfo):
        """packetInfo = (clock, moteId, packet, channel, power)"""
        clock, moteId, packet, channel, power = packetInfo
        linkQual = power
        self.counter += 1
        timestamp = long((clock + self.refClock + NTP_DELTA) * (2 ** 32))
    
        packetType = 1 # data

        Zep1 = ord('E')
        Zep2 = ord('X')
        ZepVer = 2
        msg = struct.pack("!BBBBBHBBQI", 
                          Zep1, Zep2, ZepVer,
                          packetType, channel, moteId,
                          0, # LQI Mode
                          linkQual, # LQI
                          timestamp, self.counter)
        msg += 10*chr(0) # reserved
        msg += struct.pack("<B", len(packet)+2) + packet + chr(0xff)*2
        self.sd.sendto(msg, ("", ZepPort))

#---------------------------------------------------------------------------
# An Observer using ZepSender
#---------------------------------------------------------------------------

class ZepSenderObserver(ZepSender):
    def __init__(self):
        ZepSender.__init__(self)

    def notifyPacket(self, info):
        infoTuple = (info["clock"], info["snifferId"], info["packet"], 
                     info["channel"], info["rssi"])
        self.sendAsZep(infoTuple)

#---------------------------------------------------------------------------
#
#---------------------------------------------------------------------------

def asHex(data):
    return " ".join(["%02x" % ord(x) for x in data])

def getHash(data):
    calc = hashlib.md5()
    calc.update(data)
    return calc.hexdigest()

class TextDisplayObserver:
    def notifyPacket(self, info):
        print info["clock"], "@%s"%info["snifferId"],
        #print getHash(info["packet"]), 
        print asHex(info["packet"])

class SmartRFSnifferSenderObserver:
    def __init__(self):
        self.sd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.startTime = time.time()
        self.packetIndex = 0

    def notifyPacket(self, info):
        Coef = 32000000
        HeaderSpec = "<BIQB"
        HeaderSize = struct.calcsize(HeaderSpec)
        flags = 0
        size = len(info["packet"])
        relTime = long((time.time() - self.startTime) * Coef)
        fcs = "XX" # XXX: not known
        
        header = struct.pack(HeaderSpec, flags, self.packetIndex, 
                             relTime, size)
        self.packetIndex += 1

        data = header + info["packet"] + fcs

        self.sd.sendto(data, ("", 5000))
        print info["clock"], "@%s"%info["snifferId"]
        #print getHash(info["packet"]), 
        #print asHex(info["packet"])

#---------------------------------------------------------------------------
# Unique
#---------------------------------------------------------------------------

class UniquePacketObserver:
    def __init__(self, observer):
        self.observer = observer
        self.maxNbPacket = 100
        self.packetHashQueue = []
        self.packetHashSet = set([])
        
    def notifyPacket(self, info):
        packetHash = getHash(info["packet"])
        if packetHash in self.packetHashSet:
            return

        self.packetHashQueue.append(packetHash)
        self.packetHashSet.add(packetHash)
        if len(self.packetHashSet) >= self.maxNbPacket:
            oldPacketHash = self.packetHashQueue.pop(0)
            self.packetHashSet.remove(oldPacketHash)

        self.observer.notifyPacket(info)

#---------------------------------------------------------------------------

class RecordPacketObserver:
    def __init__(self, fileName, observer=None):
        self.f = open(fileName, "w")
        self.observer = observer

    def notifyPacket(self, info):
        self.f.write(repr(info)+"\n")
        self.f.flush()
        if self.observer != None:
            self.observer.notifyPacket(info)
        
    # XXX: self.f.close() at exit

class TeePacketObserver:
    def __init__(self, observer1, observer2):
        self.observer1 = observer1
        self.observer2 = observer2

    def notifyPacket(self, info):
        self.observer1.notifyPacket(info)
        self.observer2.notifyPacket(info)

#---------------------------------------------------------------------------

def toSnifFormat(info):
    infoType = (FieldFlags["crcOk"] | FieldFlags["lqi"] 
                | FieldFlags["rssi"])
    r = "SNIF" 
    r += struct.pack("BB", infoType, len(info["packet"])) + info["packet"]
    r += struct.pack("BBB", info["crcOk"], info["rssi"], info["lqi"])
    return r



class SocatObserver:
    def __init__(self, fileName=None):
        link = "/tmp/myttyS0" # XXX
        cmd = "socat STDIN pty,link=%s,raw" % (link)
        print "+", cmd
        self.socatProcess = subprocess.Popen(
            cmd.split(" "),
            close_fds=True,
            stdin=subprocess.PIPE,
            stdout=None,
            stderr=None
            )
        
        #self.checkParser = Foren6SnifferParser("dbg", TextDisplayObserver())

    def notifyPacket(self, info):
        snifFormatPacket = toSnifFormat(info)
        #self.checkParser.notifyData(snifFormatPacket)
        self.socatProcess.stdin.write(snifFormatPacket)

    # XXX: self.socatProcess stop at exit

#---------------------------------------------------------------------------
