# -*- coding:utf-8 -*-

# This file is a part of IoT-LAB gateway_code
# Copyright (C) 2015 INRIA (Contact: admin@iot-lab.info)
# Contributor(s) : see AUTHORS file
#
# This software is governed by the CeCILL license under French law
# and abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# http://www.cecill.info.
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.

""" Roomba500 turtlebot
Python interface for the iRobot Roomba 5xx

inspired of create..py Zach Dodds   dodds@cs.hmc.edu
updated for Roomba500 by INRIA 07/08/13
Manage sending commands and receiving messages
"""

# pylint: disable=too-many-locals,bare-except
# pylint: disable=too-many-branches,too-many-statements

import math
import time
import multiprocessing

import serial

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
# MOTORS = chr(138)  # + 1 byte : motors-state   not used in turtlebot
LEDS = chr(139)     # + 3 bytes : leds-state,power-color,power-intensity
SONG = chr(140)     # + 2N+2 bytes: song-num, song-lenght:N=number of notes
PLAY = chr(141)     # + 1 byte : song-num
SENSORS = chr(142)  # + 1 byte : packet
FORCESEEKINGDOCK = chr(143)  # Dock automatique mode
# not used in turtlebot
# PWMMOTORS = chr(144)  # + 3 bytes : main brush, side brush, vaccuum
DRIVEDIRECT = chr(145)  # + 4 bytes : right-vel-high/low,left-vel-high/low
PWMDRIVE = chr(146)     # + 4 bytes :right-pwm-high/low,left-pwm-hight/low
STREAM = chr(148)       # periodic stream of sensors
QUERYLIST = chr(149)
DOSTREAM = chr(150)
BUTTONS = chr(165)      # +1 byte: buttons, virtual press of Roomba buttons

# Sensors
BUMPS_WHEELDROPS = 7
WALL = 8
CLIFF_LEFT = 9
CLIFF_FRONT_LEFT = 10
CLIFF_FRONT_RIGHT = 11
CLIFF_RIGHT = 12
VIRTUAL_WALL = 13
OVERCURRENTS = 14
# DIRT_DETECT = 15 unused in turtlebot
# 16 : unused byte
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
# 32 : used only on Create
# 33 : used only on Create
CHARGING_SOURCES_AVAILABLE = 34
OI_MODE = 35
SONG_NUMBER = 36
SONG_PLAYING = 37
NUM_STREAM_PACKETS = 38
REQUESTED_VELOCITY = 39
REQUESTED_RADIUS = 40
REQUESTED_RIGHT_VELOCITY = 41
REQUESTED_LEFT_VELOCITY = 42
LEFT_ENCODER = 43  # left and Right encodeur inverted in datasheet (not here)
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
# MAIN_BRUSH_MOTOR_CURRENT = 56 unused in turtlebot
# SIDE_BRUSH_MOTOR_CURRENT = 57 unused in turtlebot
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


# Fonctions to transform bytes/int
def two_bytes_signed_int(h_byte, l_byte):
    """ Return the value of the two bytes signed in one integer """

    double_bytes = (h_byte << 8) + l_byte
    top_bit = (double_bytes >> 15) & 0x0001
    if top_bit == 1:
        signed_value = double_bytes - 1 - 0xFFFF
    else:
        signed_value = double_bytes & 0x7FFF

    return signed_value


def two_bytes_unsigned_int(h_byte, l_byte):
    """ Return the value of the two bytes unsigned in one integer """

    return (h_byte << 8) + l_byte


def int_in_signed_bytes(integer):
    """ Return the value of the integer in two bytes,
    high byte first, signed
    """

    if integer < 0:
        integer = 0xFFFF + integer + 1

    return((integer >> 8) & 0xFF, integer & 0xFF)


class Roomba500(object):
    """ the Roomba class is an abstraction of the iRobot Roomba500's
        ROI interface, including communication and a bit
        of processing of the strings passed back and forth

        when you create an object of type Roomba, the code
        will try to open a connection to it - so, it will fail
        if it's not attached!
    """

    def __init__(self, portcom):
        """ the constructor which tries to open the
            connection to the robot at port portcom
        """
        # to do: find the shortest safe serial timeout value...
        # to do: use the timeout to do more error checking than
        #        is currently done...
        # multiprocessing for position and sensor
        self.qsens = multiprocessing.Queue()
        # multiprocessing for position and sensor
        self.qsend = multiprocessing.Queue()
        self.serial_run = False

        # test if the system is Windows or Mac/Linux
        if isinstance(portcom, str) is True:
            # system : Mac/Linux
            print 'In Mac/Linux mode...'
            self.ser = serial.Serial(portcom, baudrate=115200, timeout=0.5)
        # otherwise, system : Windows
        else:
            print 'In Windows mode...'
            self.ser = serial.Serial(portcom - 1, baudrate=115200, timeout=3)
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

        # pose of the Roomba : x (mm), y (mm), th (degrees)
        self.pose = [0.0, 0.0, 0.0]

        time.sleep(0.3)
        self.wakeup()   # wakeup the Roomba
        self.start()   # go to passive mode
        time.sleep(0.3)

    def get_sensor(self, packet_group=100):
        """ Gets back a list of sensor data """

        self.ser.write(SENSORS)
        self.ser.write(chr(packet_group))

        if packet_group == 0:
            rep = self.ser.read(size=26) + 54 * chr(0)

        if packet_group == 1:
            rep = self.ser.read(size=10) + 70 * chr(0)

        if packet_group == 2:
            rep = 10 * chr(0) + self.ser.read(size=6) + 64 * chr(0)

        if packet_group == 3:
            rep = 16 * chr(0) + self.ser.read(size=10) + 54 * chr(0)

        if packet_group == 4:
            rep = 26 * chr(0) + self.ser.read(size=14) + 40 * chr(0)

        if packet_group == 5:
            rep = 40 * chr(0) + self.ser.read(size=12) + 28 * chr(0)

        if packet_group == 6:
            rep = self.ser.read(size=52) + 28 * chr(0)

        if packet_group == 100:
            rep = self.ser.read(size=80)

        if packet_group == 101:
            rep = 52 * chr(0) + self.ser.read(size=28)

        if packet_group == 106:
            rep = 57 * chr(0) + self.ser.read(size=12) + 11 * chr(0)

        if packet_group == 107:
            rep = 71 * chr(0) + self.ser.read(size=9)

        # need error checking or sanity checking or something!

        self.sensorl = [None,
                        # 1
                        None,
                        # 2
                        None,
                        # 3
                        None,
                        # 4
                        None,
                        # 5
                        None,
                        # 6
                        None,
                        # BUMPS_WHEELDROPS = 7
                        ord(rep[0]),
                        # WALL = 8
                        ord(rep[1]) & 0x01,
                        # CLIFF_LEFT = 9
                        ord(rep[2]) & 0x01,
                        # CLIFF_FRONT_LEFT = 10
                        ord(rep[3]) & 0x01,
                        # CLIFF_FRONT_RIGHT = 11
                        ord(rep[4]) & 0x01,
                        # CLIFF_RIGHT = 12
                        ord(rep[5]) & 0x01,
                        # VIRTUAL_WALL = 13
                        ord(rep[6]) & 0x01,
                        # OVERCURRENTS = 14
                        ord(rep[7]),
                        # 15
                        None,
                        # 16
                        None,
                        # INFRARED = 17
                        ord(rep[10]),
                        # BUTTONS = 18
                        ord(rep[11]),
                        # DISTANCE = 19
                        two_bytes_signed_int(ord(rep[12]), ord(rep[13])),
                        # ANGLE = 20
                        two_bytes_signed_int(ord(rep[14]), ord(rep[15])),
                        # CHARGING_STATE = 21
                        ord(rep[16]),
                        # VOLTAGE = 22
                        two_bytes_unsigned_int(ord(rep[17]), ord(rep[18])),
                        # CURRENT = 23
                        two_bytes_signed_int(ord(rep[19]), ord(rep[20])),
                        # BATTERY_TEMP = 24
                        ord(rep[21]),
                        # BATTERY_CHARGE = 25
                        two_bytes_unsigned_int(ord(rep[22]), ord(rep[23])),
                        # BATTERY_CAPACITY = 26
                        two_bytes_unsigned_int(ord(rep[24]), ord(rep[25])),
                        # WALL_SIGNAL = 27
                        two_bytes_unsigned_int(ord(rep[26]), ord(rep[27])),
                        # CLIFF_LEFT_SIGNAL = 28
                        two_bytes_unsigned_int(ord(rep[28]), ord(rep[29])),
                        # CLIFF_FRONT_LEFT_SIGNAL = 29
                        two_bytes_unsigned_int(ord(rep[30]), ord(rep[31])),
                        # CLIFF_FRONT_RIGHT_SIGNAL = 30
                        two_bytes_unsigned_int(ord(rep[32]), ord(rep[33])),
                        # CLIFF_RIGHT_SIGNAL = 31
                        two_bytes_unsigned_int(ord(rep[34]), ord(rep[35])),
                        # 32
                        None,
                        # 33: 2 bytes
                        None,
                        # CHARGING_SOURCES_AVAILABLE = 34
                        ord(rep[39]),
                        # OI_MODE = 35
                        ord(rep[40]),
                        # SONG_NUMBER = 36
                        ord(rep[41]),
                        # SONG_PLAYING = 37
                        ord(rep[42]) & 0x01,
                        # NUM_STREAM_PACKETS = 38
                        ord(rep[43]),
                        # REQUESTED_VELOCITY = 39
                        two_bytes_signed_int(ord(rep[44]), ord(rep[45])),
                        # REQUESTED_RADIUS = 40
                        two_bytes_signed_int(ord(rep[46]), ord(rep[47])),
                        # REQUESTED_RIGHT_VELOCITY = 41
                        two_bytes_signed_int(ord(rep[48]), ord(rep[49])),
                        # REQUESTED_LEFT_VELOCITY = 42
                        two_bytes_signed_int(ord(rep[50]), ord(rep[51])),
                        # LEFT_ENCODER = 43
                        two_bytes_unsigned_int(ord(rep[52]), ord(rep[53])),
                        # RIGHT_ENCODER = 44
                        two_bytes_unsigned_int(ord(rep[54]), ord(rep[55])),
                        # LIGHT_BUMPER = 45
                        ord(rep[56]),
                        # LIGHT_BUMP_LEFT_SIGNAL = 46
                        two_bytes_unsigned_int(ord(rep[57]), ord(rep[58])),
                        # LIGHT_BUMP_FRONT_LEFT_SIGNAL = 47
                        two_bytes_unsigned_int(ord(rep[59]), ord(rep[60])),
                        # LIGHT_BUMP_CENTER_LEFT_SIGNAL = 48
                        two_bytes_unsigned_int(ord(rep[61]), ord(rep[62])),
                        # LIGHT_BUMP_CENTER_RIGHT_SIGNAL = 49
                        two_bytes_unsigned_int(ord(rep[63]), ord(rep[64])),
                        # LIGHT_BUMP_FRONT_RIGHT_SIGNAL = 50
                        two_bytes_unsigned_int(ord(rep[65]), ord(rep[66])),
                        # LIGHT_BUMP_RIGHT_SIGNAL = 51
                        two_bytes_unsigned_int(ord(rep[67]), ord(rep[68])),
                        # INFRARED_LEFT = 52
                        ord(rep[69]),
                        # INFRARED_RIGHT = 53
                        ord(rep[70]),
                        # LEFT_MOTOR_CURRENT = 54
                        two_bytes_signed_int(ord(rep[71]), ord(rep[72])),
                        # RIGHT_MOTOT_CURRENT = 55
                        two_bytes_signed_int(ord(rep[73]), ord(rep[74])),
                        # MAIN_BRUSH_MOTOR_CURRENT = 56 unused in turtlebot
                        None,
                        # SIDE_BRUSH_MOTOR_CURRENT = 57 unused in turtlebot
                        None,
                        # STASIS = 58
                        ord(rep[79]) & 0x01,
                        # LEFT_BUMP = 59
                        (ord(rep[0]) >> 1) & 0x01,
                        # RIGHT_BUMP = 60
                        (ord(rep[0]) >> 0) & 0x01,
                        # LEFT_WHEEL_DROP = 61
                        (ord(rep[0]) >> 3) & 0x01,
                        # RIGHT_WHEEL_DROP = 62
                        (ord(rep[0]) >> 2) & 0x01,
                        # HOME_BASE = 63
                        (ord(rep[39]) >> 1) & 0x01,
                        # INTERNAL_CHARGER = 64
                        (ord(rep[39]) >> 0) & 0x01,
                        # LIGHT_BUMP_LEFT = 65
                        (ord(rep[56]) >> 0) & 0x01,
                        # LIGHT_BUMP_FRONT_LEFT = 66
                        (ord(rep[56]) >> 1) & 0x01,
                        # LIGHT_BUMP_CENTER_LEFT = 67
                        (ord(rep[56]) >> 2) & 0x01,
                        # LIGHT_BUMP_CENTER_RIGHT = 68
                        (ord(rep[56]) >> 3) & 0x01,
                        # LIGHT_BUMP_FRONT_RIGHT = 69
                        (ord(rep[56]) >> 4) & 0x01,
                        # LIGHT_BUMP_RIGHT = 70
                        (ord(rep[56]) >> 5) & 0x01,
                        # LEFT_WHEEL_OVERCURRENT = 71
                        (ord(rep[7]) >> 4) & 0x01,
                        # RIGHT_WHEEL_OVERCURRENT = 72
                        (ord(rep[7]) >> 3) & 0x01,
                        # DOCK = 73
                        (ord(rep[11]) >> 2) & 0x01,
                        # SPOT = 74
                        (ord(rep[11]) >> 1) & 0x01,
                        # CLEAN = 75
                        (ord(rep[11]) >> 0) & 0x01,
                        # POS_X = 76
                        None,
                        # POS_Y = 77
                        None,
                        # POS_Z = 78
                        None]

        return self.sensorl

    def wakeup(self):
        """ wake-up the robot to off mode """

        self.ser.setRTS(0)
        time.sleep(0.5)
        self.ser.setRTS(1)
        time.sleep(0.5)
        self.ser.setRTS(0)

        return

    def start(self):
        """ changes from off mode to passive mode """

        self.ser.write(START)
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
        self.change_mode('power')   # power off the robot
        time.sleep(0.1)
        self.ser.close()
        print 'The Roomba seems to have shutdown normally'

        return

    def change_mode(self, mode):
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
            self.ser.write(SAFE)
            time.sleep(0.025)

        if mode == 'full':
            self.ser.write(FULL)
            time.sleep(0.025)

        if mode == 'power':
            self.ser.write(POWER)
            time.sleep(0.025)

        if mode == 'spot':
            # here there is an error when we write SPOT ???
            self.ser.write(chr(134))
            time.sleep(0.025)

        if mode == 'clean':
            # here there is an error when we write CLEAN ???
            self.ser.write(chr(135))
            time.sleep(0.025)

        if mode == 'max':
            self.ser.write(MAX)
            time.sleep(0.025)

        if mode == 'dock':
            self.ser.write(FORCESEEKINGDOCK)
            time.sleep(0.025)

        return

    def drive_direct(self, right_velocity, left_velocity):
        """ Control right and left wheels velocity """

        rv_high_byte, rv_low_byte = int_in_signed_bytes(right_velocity)
        lv_high_byte, lv_low_byte = int_in_signed_bytes(left_velocity)

        self.ser.write(DRIVEDIRECT)
        self.ser.write(chr(rv_high_byte))
        self.ser.write(chr(rv_low_byte))
        self.ser.write(chr(lv_high_byte))
        self.ser.write(chr(lv_low_byte))

        return

    def drive(self, velocity, radius):
        """ Control wheels velocity with drive function """

        v_high_byte, v_low_byte = int_in_signed_bytes(velocity)
        r_high_byte, r_low_byte = int_in_signed_bytes(radius)

        self.ser.write(DRIVE)
        self.ser.write(chr(v_high_byte))
        self.ser.write(chr(v_low_byte))
        self.ser.write(chr(r_high_byte))
        self.ser.write(chr(r_low_byte))

        return

    def song(self, song_number, notes_and_durations):
        """ Load a song """

        # notes_and_durations must be a list like this :
        # [note1, duration1, note2, duration2, ...]
        self.ser.write(SONG)
        self.ser.write(chr(song_number))
        self.ser.write(chr(len(notes_and_durations) / 2))

        for value in notes_and_durations:
            self.ser.write(chr(value))

        return

    def play(self, song_number):
        """ Play a song """
        self.ser.write(PLAY)
        self.ser.write(chr(song_number))

        return

    def led(self, leds_val):
        """ Control Roomba leds """
        check_robot = leds_val[0]
        dock = leds_val[1]
        spot = leds_val[2]
        debri = leds_val[3]
        led_color = leds_val[4]
        led_intensity = leds_val[5]

        leds_byte = debri + (spot * 2) + (dock * 4) + (check_robot * 8)

        self.ser.write(LEDS)
        self.ser.write(chr(leds_byte))
        # for the clean/power led
        self.ser.write(chr(led_color))
        # for the clean/power led
        self.ser.write(chr(led_intensity))

        return

    def buttons(self, but_val):
        """ Virtual puch on Roomba buttons """

        clock = but_val[0]
        schedule = but_val[1]
        day = but_val[2]
        hour = but_val[3]
        minute = but_val[4]
        dock = but_val[5]
        spot = but_val[6]
        clean = but_val[7]
        # this command seems to doesn't work in safe/full mode...
        button_byte = clean + (spot * 2) + (dock * 4) + (minute * 8) + \
            (hour * 16) + (day * 32) + (schedule * 64) + (clock * 128)
        # here there is an error when we write BUTTONS ???
        self.ser.write(chr(165))
        self.ser.write(chr(button_byte))

        return

    def reset_position(self):
        """ Reset the current position to 0, 0, (mm) 0 (degrees) """
        self.pose = [0.0, 0.0, 0.0]

        return

    def set_position(self, spx, spy, spz):
        """ Set the current position to x, y, theta """
        self.pose[0] = spx
        self.pose[1] = spy
        self.pose[2] = spz

        return

    def interface_serial(self):
        """ Interface for serial connection
            Run this function in backgrown process with multiprocessing
            and use Queue for get the position and sensor and send
            command to Roomba
        """
        sens = self.get_sensor()
        init_right = sens[RIGHT_ENCODER]
        init_left = sens[LEFT_ENCODER]

        codeur_right = 0
        codeur_left = 0

        prev_raw_right_encoder = init_right
        prev_raw_left_encoder = init_left

        prev_dist = 0
        prev_angle = 0

        i = 0
        j = 0

        self.sensorl[POS_X] = self.pose[0]
        self.sensorl[POS_Y] = self.pose[1]
        self.sensorl[POS_Z] = self.pose[2]

        self.qsens.put(self.sensorl)

        while self.serial_run is True:
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
                    valu = send['change_mode']
                    self.change_mode(valu)

                except KeyError:
                    pass

                try:
                    valu = send['drive_direct']
                    self.drive_direct(valu[0], valu[1])

                except KeyError:
                    pass

                try:
                    valu = send['drive']
                    self.drive(valu[0], valu[1])

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
                    self.led(valu)

                except KeyError:
                    pass

                try:
                    valu = send['buttons']
                    self.buttons(valu)

                except KeyError:
                    pass

                try:
                    valu = send['reset_position']
                    self.reset_position()

                except KeyError:
                    pass

            except:  # noqa: E722
                pass

            sens = self.get_sensor()
            # if number pass to 0 at 65535...
            if (sens[RIGHT_ENCODER] - prev_raw_right_encoder) > 60000:
                i += -1
            # if number pass to 65535 at 0...
            elif (sens[RIGHT_ENCODER] - prev_raw_right_encoder) < -60000:
                i += 1
            # if number pass to 0 at 65535...
            if (sens[LEFT_ENCODER] - prev_raw_left_encoder) > 60000:
                j += -1
            # if number pass to 65535 at 0...
            elif (sens[LEFT_ENCODER] - prev_raw_left_encoder) < -60000:
                j += 1
            # the value 60000 depend of time between each get_sensor...
            codeur_right = sens[RIGHT_ENCODER] + i * 65535 - init_right
            codeur_left = sens[LEFT_ENCODER] + j * 65535 - init_left

            distance = ((codeur_right + codeur_left) / 1024.0)
            distance = distance * 72.90853488 * math.pi

            # 72.90853488 is the diameter of the wheels with a corection in mm,
            # there are 512 points per turn in the encoders distance in mm
            angle = ((codeur_right - codeur_left) / 1024.0)
            angle = (angle * 79.97155157 * 360) / 258

            # 258 is the distance between wheels in mm, 79.97155157 is the
            # diameter of the wheels with a corection in mm angle in degrees
            theta = math.radians(angle)

            ddist = (distance - prev_dist)
            self.pose[0] = self.pose[0] + (ddist * math.cos(theta))
            self.pose[1] = self.pose[1] + (ddist * math.sin(theta))
            self.pose[2] = self.pose[2] + (angle - prev_angle)

            self.sensorl[POS_X] = self.pose[0]
            self.sensorl[POS_Y] = self.pose[1]
            self.sensorl[POS_Z] = self.pose[2]

            try:
                if self.qsens.qsize > 0:
                    self.qsens.get_nowait()
            except:  # noqa: E722
                pass
            # Put the value of all sensors and position
            # of the Roomba with Queue
            self.qsens.put(self.sensorl)

            # print position
            # print(self.sensorl[POS_X],\
            # self.sensorl[POS_Y], self.sensorl[POS_Z])

            prev_raw_right_encoder = sens[RIGHT_ENCODER]
            prev_raw_left_encoder = sens[LEFT_ENCODER]

            prev_dist = distance
            prev_angle = angle

            time.sleep(0.015)
