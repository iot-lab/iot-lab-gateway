#
# roomba500 turtlebot
#
# Python interface for the iRobot Roomba 5xx
#
# inspired of create..py Zach Dodds   dodds@cs.hmc.edu
# updated for Roomba500 by INRIA 2/07/12
#

import serial
import math
import time
import multiprocessing

# some module-level definitions for the robot commands
START = chr(128)    # already converted to bytes...
BAUD = chr(129)     # + 1 byte (baud-code)
SAFE = chr(131)
FULL = chr(132)
POWER = chr(133)    # Set the power-off
SPOT = chr(134)     # Spot automatic mode
CLEAN = chr(135)    # Clean automatic mode
MAX = chr(136)      # Max clean automatic mode
DRIVE = chr(137)    # + 4 bytes : vel-high/low,radius-high/low
#MOTORS = chr(138)  # + 1 byte : motors-state   not used in turtlebot
LEDS = chr(139)     # + 3 bytes : leds-state,power-color,power-intensity
SONG = chr(140)     # + 2N+2 bytes: song-num, song-lenght:N=number of notes
PLAY = chr(141)     # + 1 byte : song-num
SENSORS = chr(142)  # + 1 byte : packet
FORCESEEKINGDOCK = chr(143)  # Dock automatique mode
#PWMMOTORS =chr(144) # + 3 bytes : main brush, side brush, vaccuum   not used in turtlebot
DRIVEDIRECT = chr(145) # + 4 bytes : right-vel-high/low,left-vel-high/low
PWMDRIVE  =chr(146) # + 4 bytes :right-pwm-high/low,left-pwm-hight/low
STREAM = chr(148)   # periodic stream of sensors
QUERYLIST= chr(149)    
DOSTREAM = chr(150)
BUTTONS  = chr(165) # +1 byte: buttons, virtual press of Roomba buttons

# Sensors
BUMPS_WHEELDROPS = 7
WALL = 8
CLIFF_LEFT = 9
CLIFF_FRONT_LEFT = 10
CLIFF_FRONT_RIGHT = 11
CLIFF_RIGHT = 12
VIRTUAL_WALL = 13
OVERCURRENTS = 14
#DIRT_DETECT = 15 unused in turtlebot
#16 : unused byte
INFRARED = 17
BUTTONS = 18
DISTANCE = 19
ANGLE = 20
CHARGING_STATE = 21
VOLTAGE = 22
CURRENT = 23
BATTERY_TEMP = 24
BATTERY_CHARGE = 25
BATTERY_CAPACITY = 26
WALL_SIGNAL = 27
CLIFF_LEFT_SIGNAL = 28
CLIFF_FRONT_LEFT_SIGNAL = 29
CLIFF_FRONT_RIGHT_SIGNAL = 30
CLIFF_RIGHT_SIGNAL = 31
#32 : used only on Create
#33 : used only on Create
CHARGING_SOURCES_AVAILABLE = 34
OI_MODE = 35
SONG_NUMBER = 36
SONG_PLAYING = 37
NUM_STREAM_PACKETS = 38
REQUESTED_VELOCITY = 39
REQUESTED_RADIUS = 40
REQUESTED_RIGHT_VELOCITY = 41
REQUESTED_LEFT_VELOCITY = 42
LEFT_ENCODER = 43   # left and Right encodeur are inverted in datasheet (not here)
RIGHT_ENCODER = 44
LIGHT_BUMPER = 45
LIGHT_BUMP_LEFT_SIGNAL = 46
LIGHT_BUMP_FRONT_LEFT_SIGNAL = 47
LIGHT_BUMP_CENTER_LEFT_SIGNAL = 48
LIGHT_BUMP_CENTER_RIGHT_SIGNAL = 49
LIGHT_BUMP_FRONT_RIGHT_SIGNAL = 50
LIGHT_BUMP_RIGHT_SIGNAL = 51
INFRARED_LEFT = 52
INFRARED_RIGHT = 53
LEFT_MOTOR_CURRENT = 54
RIGHT_MOTOT_CURRENT = 55
#MAIN_BRUSH_MOTOR_CURRENT = 56 unused in turtlebot
#SIDE_BRUSH_MOTOR_CURRENT = 57 unused in turtlebot
STASIS = 58

# others just for easy access to particular parts of the data
LEFT_BUMP = 59
RIGHT_BUMP = 60
LEFT_WHEEL_DROP = 61
RIGHT_WHEEL_DROP = 62
HOME_BASE = 63
INTERNAL_CHARGER = 64
LIGHT_BUMP_LEFT = 65
LIGHT_BUMP_FRONT_LEFT = 66
LIGHT_BUMP_CENTER_LEFT = 67
LIGHT_BUMP_CENTER_RIGHT = 68
LIGHT_BUMP_FRONT_RIGHT = 69
LIGHT_BUMP_RIGHT = 70
LEFT_WHEEL_OVERCURRENT = 71
RIGHT_WHEEL_OVERCURRENT = 72
DOCK = 73
SPOT = 74
CLEAN = 75

# for have the raw of the position in the list sensorl
POS_X = 76
POS_Y = 77
POS_Z = 78


#
# the robot class
#
class Roomba500:
    """ the Roomba class is an abstraction of the iRobot Roomba500's
        ROI interface, including communication and a bit
        of processing of the strings passed back and forth
        
        when you create an object of type Roomba, the code
        will try to open a connection to it - so, it will fail
        if it's not attached!
    """

    def __init__(self, PORT):
        """ the constructor which tries to open the
            connection to the robot at port PORT
        """
        # to do: find the shortest safe serial timeout value...
        # to do: use the timeout to do more error checking than
        #        is currently done...

        self.q = multiprocessing.Queue()   # multiprocessing for position and sensor
        self.qsend = multiprocessing.Queue()   # multiprocessing for position and sensor
        self.serial_run = False

        # test if the system is Windows or Mac/Linux
        if type(PORT) == type('string'):
            # system : Mac/Linux
            print 'In Mac/Linux mode...'
            self.ser = serial.Serial(PORT, baudrate=115200, timeout=0.5)
        # otherwise, system : Windows
        else:
            print 'In Windows mode...'
            self.ser = serial.Serial(PORT-1, baudrate=115200, timeout=3)
            # the -1 here is because windows starts counting from 1
            # in the hardware control panel, but not in pyserial, it seems

        # did the serial port actually open?
        if self.ser.isOpen():
            print 'Serial port did open, presumably to a roomba...'
            self.connect = True
        else:
            print 'Serial port did NOT open, check the'
            print '  - port number'
            print '  - physical connection'
            print '  - baud rate of the roomba (it\'s possible, if unlikely,'
            print '            that the baud rate is not 115200 - removing and'
            print '            reinstalling the battery should reset it.'
            self.connect = False

        # our sensor list, currently empty
        self.sensorl = []

        # position of the Roomba
        self.x = 0.0   # mm
        self.y = 0.0   # mm
        self.z = 0.0   # degrees

        time.sleep(0.3)
        self.wakeup()   # wakeup the Roomba
        self.start()   # go to passive mode
        time.sleep(0.3)


    def twoBytesSignedInInt(self, hByte, lByte):
        """ Return the value of the two bytes signed in one integer """

        doubleBytes = (hByte << 8) + lByte
        topBit = (doubleBytes >> 15) & 0x0001
        if topBit == 1:
            doubleBytes = doubleBytes - 1
            return doubleBytes - 0xFFFF
            
        else:
            return doubleBytes & 0x7FFF


    def twoBytesUnsignedInInt(self, hByte, lByte):
        """ Return the value of the two bytes unsigned in one integer """

        return (hByte << 8) + lByte


    def intInSignedBytes(self, integer):
        """ Return the value of the integer in two bytes,
            high byte first, signed
        """

        if integer < 0:
            integer = 0xFFFF + integer + 1

        return( (integer >> 8) & 0xFF, integer & 0xFF )


    def getSensor(self, packetGroup=100):
        """ Gets back a list of sensor data """

        self.ser.write( SENSORS )
        self.ser.write( chr(packetGroup) )

        if packetGroup == 0:
            r = self.ser.read(size=26) + 54*chr(0)

        if packetGroup == 1:
            r = self.ser.read(size=10) + 70*chr(0)

        if packetGroup == 2:
            r = 10*chr(0) + self.ser.read(size=6) + 64*chr(0)

        if packetGroup == 3:
            r = 16*chr(0) + self.ser.read(size=10) + 54*chr(0)

        if packetGroup == 4:
            r = 26*chr(0) + self.ser.read(size=14) + 40*chr(0)

        if packetGroup == 5:
            r = 40*chr(0) + self.ser.read(size=12) + 28*chr(0)

        if packetGroup == 6:
            r = self.ser.read(size=52) + 28*chr(0)

        if packetGroup == 100:
            r = self.ser.read(size=80)

        if packetGroup == 101:
            r = 52*chr(0) + self.ser.read(size=28)

        if packetGroup == 106:
            r = 57*chr(0) + self.ser.read(size=12) + 11*chr(0)

        if packetGroup == 107:
            r = 71*chr(0) + self.ser.read(size=9)

        # need error checking or sanity checking or something!


        self.sensorl = [ None,   #0
                         None,   #1
                         None,   #2
                         None,   #3
                         None,   #4
                         None,   #5
                         None,   #6
                         ord(r[0]),   #BUMPS_WHEELDROPS = 7
                         ord(r[1]) & 0x01,   #WALL = 8
                         ord(r[2]) & 0x01,   #CLIFF_LEFT = 9
                         ord(r[3]) & 0x01,   #CLIFF_FRONT_LEFT = 10
                         ord(r[4]) & 0x01,   #CLIFF_FRONT_RIGHT = 11
                         ord(r[5]) & 0x01,   #CLIFF_RIGHT = 12
                         ord(r[6]) & 0x01,   #VIRTUAL_WALL = 13
                         ord(r[7]),   #OVERCURRENTS = 14
                         None,   #15
                         None,   #16
                         ord(r[10]),   #INFRARED = 17
                         ord(r[11]),   #BUTTONS = 18
                         self.twoBytesSignedInInt(ord(r[12]), ord(r[13])),   #DISTANCE = 19
                         self.twoBytesSignedInInt(ord(r[14]), ord(r[15])),   #ANGLE = 20
                         ord(r[16]),   #CHARGING_STATE = 21
                         self.twoBytesUnsignedInInt(ord(r[17]), ord(r[18])),   #VOLTAGE = 22
                         self.twoBytesSignedInInt(ord(r[19]), ord(r[20])),   #CURRENT = 23
                         ord(r[21]),   #BATTERY_TEMP = 24
                         self.twoBytesUnsignedInInt(ord(r[22]), ord(r[23])),   #BATTERY_CHARGE = 25
                         self.twoBytesUnsignedInInt(ord(r[24]), ord(r[25])),   #BATTERY_CAPACITY = 26
                         self.twoBytesUnsignedInInt(ord(r[26]), ord(r[27])),   #WALL_SIGNAL = 27
                         self.twoBytesUnsignedInInt(ord(r[28]), ord(r[29])),   #CLIFF_LEFT_SIGNAL = 28
                         self.twoBytesUnsignedInInt(ord(r[30]), ord(r[31])),   #CLIFF_FRONT_LEFT_SIGNAL = 29
                         self.twoBytesUnsignedInInt(ord(r[32]), ord(r[33])),   #CLIFF_FRONT_RIGHT_SIGNAL = 30
                         self.twoBytesUnsignedInInt(ord(r[34]), ord(r[35])),   #CLIFF_RIGHT_SIGNAL = 31
                         None,   #32
                         None,   #33 : 2 bytes
                         ord(r[39]),   #CHARGING_SOURCES_AVAILABLE = 34
                         ord(r[40]),   #OI_MODE = 35
                         ord(r[41]),   #SONG_NUMBER = 36
                         ord(r[42]) & 0x01,   #SONG_PLAYING = 37
                         ord(r[43]),   #NUM_STREAM_PACKETS = 38
                         self.twoBytesSignedInInt(ord(r[44]), ord(r[45])),   #REQUESTED_VELOCITY = 39
                         self.twoBytesSignedInInt(ord(r[46]), ord(r[47])),   #REQUESTED_RADIUS = 40
                         self.twoBytesSignedInInt(ord(r[48]), ord(r[49])),   #REQUESTED_RIGHT_VELOCITY = 41
                         self.twoBytesSignedInInt(ord(r[50]), ord(r[51])),   #REQUESTED_LEFT_VELOCITY = 42
                         self.twoBytesUnsignedInInt(ord(r[52]), ord(r[53])),   #LEFT_ENCODER = 43
                         self.twoBytesUnsignedInInt(ord(r[54]), ord(r[55])),   #RIGHT_ENCODER = 44
                         ord(r[56]),   #LIGHT_BUMPER = 45
                         self.twoBytesUnsignedInInt(ord(r[57]), ord(r[58])),   #LIGHT_BUMP_LEFT_SIGNAL = 46
                         self.twoBytesUnsignedInInt(ord(r[59]), ord(r[60])),   #LIGHT_BUMP_FRONT_LEFT_SIGNAL = 47
                         self.twoBytesUnsignedInInt(ord(r[61]), ord(r[62])),   #LIGHT_BUMP_CENTER_LEFT_SIGNAL = 48
                         self.twoBytesUnsignedInInt(ord(r[63]), ord(r[64])),   #LIGHT_BUMP_CENTER_RIGHT_SIGNAL = 49
                         self.twoBytesUnsignedInInt(ord(r[65]), ord(r[66])),   #LIGHT_BUMP_FRONT_RIGHT_SIGNAL = 50
                         self.twoBytesUnsignedInInt(ord(r[67]), ord(r[68])),   #LIGHT_BUMP_RIGHT_SIGNAL = 51
                         ord(r[69]),   #INFRARED_LEFT = 52
                         ord(r[70]),   #INFRARED_RIGHT = 53
                         self.twoBytesSignedInInt(ord(r[71]), ord(r[72])),   #LEFT_MOTOR_CURRENT = 54
                         self.twoBytesSignedInInt(ord(r[73]), ord(r[74])),   #RIGHT_MOTOT_CURRENT = 55
                         None,   #MAIN_BRUSH_MOTOR_CURRENT = 56 unused in turtlebot
                         None,   #SIDE_BRUSH_MOTOR_CURRENT = 57 unused in turtlebot
                         ord(r[79]) & 0x01,   #STASIS = 58
                         (ord(r[0]) >> 1) & 0x01,   #LEFT_BUMP = 59
                         (ord(r[0]) >> 0) & 0x01,   #RIGHT_BUMP = 60
                         (ord(r[0]) >> 3) & 0x01,   #LEFT_WHEEL_DROP = 61
                         (ord(r[0]) >> 2) & 0x01,   #RIGHT_WHEEL_DROP = 62
                         (ord(r[39]) >> 1) & 0x01,   #HOME_BASE = 63
                         (ord(r[39]) >> 0) & 0x01,   #INTERNAL_CHARGER = 64
                         (ord(r[56]) >> 0) & 0x01,   #LIGHT_BUMP_LEFT = 65
                         (ord(r[56]) >> 1) & 0x01,   #LIGHT_BUMP_FRONT_LEFT = 66
                         (ord(r[56]) >> 2) & 0x01,   #LIGHT_BUMP_CENTER_LEFT = 67
                         (ord(r[56]) >> 3) & 0x01,   #LIGHT_BUMP_CENTER_RIGHT = 68
                         (ord(r[56]) >> 4) & 0x01,   #LIGHT_BUMP_FRONT_RIGHT = 69
                         (ord(r[56]) >> 5) & 0x01,   #LIGHT_BUMP_RIGHT = 70
                         (ord(r[7]) >> 4) & 0x01,   #LEFT_WHEEL_OVERCURRENT = 71
                         (ord(r[7]) >> 3) & 0x01,   #RIGHT_WHEEL_OVERCURRENT = 72
                         (ord(r[11]) >> 2) & 0x01,   #DOCK = 73
                         (ord(r[11]) >> 1) & 0x01,   #SPOT = 74
                         (ord(r[11]) >> 0) & 0x01,   #CLEAN = 75
                         None,   #POS_X = 76
                         None,   #POS_Y = 77
                         None ]  #POS_Z = 78

        return self.sensorl


    def wakeup(self):
      """ wake-up the robot to off mode """

      self.ser.setRTS (0)
      time.sleep (0.5)
      self.ser.setRTS (1)
      time.sleep (0.5)
      self.ser.setRTS (0)

      return


    def start(self):
        """ changes from off mode to passive mode """

        self.ser.write( START )
        # they recommend 20 ms between mode-changing commands
        time.sleep(0.025)

        return


    def close(self):
        """ Tries to shutdown the robot as kindly as possible, by
            going to passive mode
            power off the Roomba
            closing the serial port
        """
        # is there other clean up to be done?
        self.connect = True

        time.sleep(0.1)
        self.start()       # send Roomba back to passive mode
        time.sleep(0.1)
        self.changeMode('power')   # power off the robot
        time.sleep(0.1)
        self.ser.close()
        print('The Roomba seems to have shutdown normally')

        return


    def changeMode(self, mode):
        """ Change the current mode :
                          safe
                          full
                          power
                          spot
                          clean
                          max
                          dock
        """  


        if mode == 'safe':
            self.ser.write( SAFE )
            time.sleep(0.025)

        if mode == 'full':
            self.ser.write( FULL )
            time.sleep(0.025)

        if mode == 'power':
            self.ser.write( POWER )
            time.sleep(0.025)

        if mode == 'spot':
            self.ser.write( chr(134) )   # here there is an error when we write SPOT ???
            time.sleep(0.025)

        if mode == 'clean':
            self.ser.write( chr(135) )   # here there is an error when we write CLEAN ???
            time.sleep(0.025)

        if mode == 'max':
            self.ser.write( MAX )
            time.sleep(0.025)

        if mode == 'dock':
            self.ser.write( FORCESEEKINGDOCK )
            time.sleep(0.025)

        return


    def driveDirect(self, rightVelocity, leftVelocity):
        """ Control right and left wheels velocity """

        rvHighByte, rvLowByte = self.intInSignedBytes(rightVelocity)
        lvHighByte, lvLowByte = self.intInSignedBytes(leftVelocity)
        
        self.ser.write( DRIVEDIRECT )
        self.ser.write( chr(rvHighByte) )
        self.ser.write( chr(rvLowByte) )
        self.ser.write( chr(lvHighByte) )
        self.ser.write( chr(lvLowByte) )

        return


    def drive(self, velocity, radius):
        """ Control wheels velocity with drive function """

        vHighByte, vLowByte = self.intInSignedBytes(velocity)
        rHighByte, rLowByte = self.intInSignedBytes(radius)
        
        self.ser.write( DRIVE )
        self.ser.write( chr(vHighByte) )
        self.ser.write( chr(vLowByte) )
        self.ser.write( chr(rHighByte) )
        self.ser.write( chr(rLowByte) )

        return


    def song(self, song_number, notes_and_durations):
        """ Load a song """

        # notes_and_durations must be a list like this : [note1, duration1, note2, duration2, ...]

        self.ser.write( SONG )
        self.ser.write( chr(song_number) )
        self.ser.write( chr(len(notes_and_durations)/2) )

        for value in notes_and_durations:
            self.ser.write( chr(value) )

        return


    def play(self, song_number):
        """ Play a song """

        self.ser.write( PLAY )
        self.ser.write( chr(song_number) )

        return


    def led(self, checkRobot, dock, spot, debri, ledColor, ledIntensity):
        """ Control Roomba leds """

        ledsByte = debri + spot*2 + dock*4 + checkRobot*8

        self.ser.write( LEDS )
        self.ser.write( chr(ledsByte) )
        self.ser.write( chr(ledColor) )   # for the clean/power led
        self.ser.write( chr(ledIntensity) )   # for the clean/power led

        return


    def buttons(self, clock, schedule, day, hour, minute, dock, spot, clean):
        """ Virtual puch on Roomba buttons """

        # this command seems to doesn't work in safe/full mode...

        buttonByte = clean + spot*2 + dock*4 + minute*8 + hour*16 + day*32 + schedule*64 + clock*128

        self.ser.write( chr(165) )   # here there is an error when we write BUTTONS ???
        self.ser.write( chr(buttonByte) )

        return


    def resetPosition(self):
        """ Reset the current position to 0, 0, 0 (mm) """

        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

        return


    def setPosition(self, x, y, z):
        """ Set the current position to x, y, z """

        self.x = x
        self.y = y
        self.z = z

        return


    def interfaceSerial(self):
        """ Interface for serial connection
            Run this function in backgrown process with multiprocessing
            and use Queue for get the position and sensor and send command to Roomba
        """

        sens = self.getSensor()

        initRight = sens[RIGHT_ENCODER]
        initLeft = sens[LEFT_ENCODER]
        
        codeurRight = 0
        codeurLeft = 0
    
        prev_raw_right_encoder = initRight
        prev_raw_left_encoder = initLeft

        prev_distance = 0
        prev_angle = 0

        i = 0
        j = 0

        self.sensorl[POS_X] = self.x
        self.sensorl[POS_Y] = self.y
        self.sensorl[POS_Z] = self.z

        self.q.put(self.sensorl)

        while self.serial_run == True :
            try:
                send = self.qsend.get_nowait()

                try:
                    valu = send['wakeup']
                    self.wakeup()
                    
                except KeyError:
                    pass

                try:
                    valu = send['start']
                    self.start()
                    
                except KeyError:
                    pass

                try:
                    valu = send['close']
                    self.close()
                    
                except KeyError:
                    pass

                try:
                    valu = send['changeMode']
                    self.changeMode(valu)
                    
                except KeyError:
                    pass

                try:
                    valu = send['driveDirect']
                    self.driveDirect(valu[0], valu[1])
                    
                except KeyError:
                    pass

                try:
                    valu = send['drive']
                    self.wakeup(valu[0], vale[1])
                    
                except KeyError:
                    pass

                try:
                    valu = send['song']
                    self.song(valu[0], valu[1])
                    
                except KeyError:
                    pass

                try:
                    valu = send['play']
                    self.play(valu)
                    
                except KeyError:
                    pass

                try:
                    valu = send['led']
                    self.led(valu[0], valu[1], valu[2], valu[3], valu[4], valu[5])
                    
                except KeyError:
                    pass

                try:
                    valu = send['buttons']
                    self.buttons(valu[0], valu[1], valu[2], valu[3], valu[4], valu[5], valu[6], valu[7])
                    
                except KeyError:
                    pass

                try:
                    valu = send['resetPosition']
                    self.resetPosition()
                    
                except KeyError:
                    pass

            except:
                pass

            sens = self.getSensor()

            if (sens[RIGHT_ENCODER] - prev_raw_right_encoder) > 60000:   # if number pass to 0 at 65535...
                i += -1

            elif (sens[RIGHT_ENCODER] - prev_raw_right_encoder) < -60000:   # if number pass to 65535 at 0...
                i += 1

            if (sens[LEFT_ENCODER] - prev_raw_left_encoder) > 60000:   # if number pass to 0 at 65535...
                j += -1

            elif (sens[LEFT_ENCODER] - prev_raw_left_encoder) < -60000:   # if number pass to 65535 at 0...
                j += 1

            # the value 60000 depend of time between each getSensor...


            codeurRight = sens[RIGHT_ENCODER] + i*65535 - initRight

            codeurLeft = sens[LEFT_ENCODER] + j*65535 - initLeft


            distance = ((codeurRight + codeurLeft) / 1024.0) * 72.90853488 * math.pi

            # 72.90853488 is the diameter of the wheels with a corection in mm, there are 512 points per turn in the encoders
            # distance in mm

            angle = (((codeurRight - codeurLeft) / 1024.0) * 79.97155157 * 360) / 258
            
            # 258 is the distance between wheels in mm, 79.97155157 is the diameter of the wheels with a corection in mm
            # angle in degrees

            th = math.radians(angle)
        
            self.x = self.x + (distance - prev_distance)*math.cos(th)
            self.y = self.y + (distance - prev_distance)*math.sin(th)
            self.z = self.z + (angle - prev_angle)

            self.sensorl[POS_X] = self.x
            self.sensorl[POS_Y] = self.y
            self.sensorl[POS_Z] = self.z


            try:
                if self.q.qsize > 0:
                    a = self.q.get_nowait()

            except:
                pass

            self.q.put(self.sensorl)   # Put the value of all sensors and position of the Roomba with Queue

            #print(self.sensorl[POS_X], self.sensorl[POS_Y], self.sensorl[POS_Z])   # print position

            prev_raw_right_encoder = sens[RIGHT_ENCODER]
            prev_raw_left_encoder = sens[LEFT_ENCODER]

            prev_distance = distance
            prev_angle = angle

            time.sleep(0.015)
