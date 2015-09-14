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


"""
Interface with roomba robot directly controled by the gateway

Manage the robot start/stop experiment, robot behavior and status
"""

from roomba import roomba
import logging
import time
import threading

# Robot status enumeration
STATUS = {'error': -1, 'closed': 0, 'init': 1, 'docked': 2,
          'moving': 3, 'paused': 4, 'searching_dock': 4}
ENERGY = {'charged': 0, 'discharged': 1}
# Parameters
LOGGER = logging.getLogger('gateway_code')
TTY = '/dev/ttyROOMBA'
BATTERY_LOW_LEVEL = 20
BATTERY_HIGH_LEVEL = 80


class GatewayRoomba(object):
    """
    Class managing the roomba robot
    """

    def __init__(self):
        self.status = 'init'
        self.battery = -1

        self.robot = None
        self.watch_thread = None
        self.watch_run = False
        self.serial_thread = None
        self.sensor_list = None

        self.init_roomba()

        return

    def init_roomba(self):
        """
        Init the Roomba communication
        """

        st_return = 0
        self.status = 'init'
        LOGGER.info('Init Roomba communication')
        # Open the serial to communicate with Roomba
        self.robot = roomba.Roomba500(TTY)
        if self.robot.connect is False:
            self.status = 'error'
            st_return = 1
            LOGGER.error('Roomba connection failed')
        else:
            # create two thread : to manage communication
            # and to watch sensors & safety
            self.watch_thread = threading.Thread(target=self._watch_roomba)
            self.robot.serial_run = True
            self.serial_thread = \
                threading.Thread(target=self.robot.interface_serial)
            self.serial_thread.start()
            # wait to establish communication
            time.sleep(1)
            self.watch_run = True
            self.watch_thread.start()

        return st_return

    def close_roomba(self):
        """
        Close Roomba communication
        """
        self.status = 'closed'
        LOGGER.info('Close Roomba communication')
        # end background thread
        self.watch_run = False
        self.watch_thread.join()
        time.sleep(1)
        self.robot.serial_run = False
        self.serial_thread.join()
        # close serial port and shutdown the Roomba
        self.robot.close()
        return 0

    def start(self):
        """
        Start experiment with Roomba
        """

        st_return = 0
        if STATUS[self.status] < 1:
            st_return = 1
            LOGGER.error('Start experiment failed')
        else:
            LOGGER.info('Start experiment')
            self.robot.qsend.put({'change_mode': 'clean'})
            self.status = 'moving'

        return st_return

    def stop(self):
        """
        Stop experiment with Roomba
        """

        st_return = 0

        if STATUS[self.status] < 1:
            st_return = 1
            LOGGER.error('Stop experiment failed')
        else:
            LOGGER.info('Stop experiment')
            self.robot.qsend.put({'change_mode': 'dock'})
            # send roomba commande twice, why ?
            time.sleep(1)
            self.robot.qsend.put({'change_mode': 'dock'})
            self.status = 'searching_dock'

        return st_return

    def get_status(self):
        """
        Get the status of  Roomba
        """

        return self.status

    def get_battery(self):
        """
        Get the level of Roomba battery
        """

        if STATUS[self.status] < 1:
            LOGGER.error('Get battery failed')
            self.battery = -1

        return self.battery

    def get_position(self):
        """
        Get the x,y,theta position of Roomba
        """

        if STATUS[self.status] < 1:
            LOGGER.error('Get position failed')
        else:
            posx = self.sensor_list[roomba.POS_X]
            posy = self.sensor_list[roomba.POS_Y]
            theta = self.sensor_list[roomba.POS_Z]

        return [posx, posy, theta]

    def motion_pause(self):
        """
        During motion, pause it
        """

        st_return = 0
        if self.status == 'moving':
            st_return = 1
            LOGGER.info('Motion pause')
            self.robot.qsend.put({'change_mode': 'safe'})
            self.status = 'paused'
        else:
            st_return = 1
            LOGGER.error('Motion pause failed')

        return st_return

    def motion_continue(self):
        """
        During a pause, continue the motion
        """

        st_return = 0
        if self.status == 'paused':
            st_return = 1
            LOGGER.info('Motion continue')
            self.robot.qsend.put({'change_mode': 'clean'})
            self.status = 'moving'
        else:
            st_return = 1
            LOGGER.error('Motion continue failed')

        return st_return

    def motion_searchdock(self):
        """
        Seek dock
        """

        st_return = 0
        if STATUS[self.status] < 1:
            st_return = 1
            LOGGER.error('Stop experiment failed')
        else:
            LOGGER.info('Stop experiment')
            self.robot.qsend.put({'change_mode': 'dock'})
            self.status = 'searching_dock'

        return st_return

    def _watch_roomba(self):
        """
        Loop to watch the status and the safety of Roomba
        """

        while self.watch_run is True:
            self.sensor_list = self.robot.qsens.get()

            # Stop directly Roomba if there is an error
            if self.status == 'error':
                self.robot.qsend.put({'change_mode': 'safe'})
                LOGGER.error('Roomba Emergency Stop')

            if STATUS[self.status] > 1:
                # Robot docking detection
                if self.sensor_list[roomba.HOME_BASE] == 1 \
                        and self.status not in ('docked', 'moving'):
                    self.status = 'docked'
                    self.robot.reset_position()
                    LOGGER.info('Docked')
                # Motors overcurrent detection
                if self.sensor_list[roomba.LEFT_WHEEL_OVERCURRENT] \
                        or self.sensor_list[roomba.RIGHT_WHEEL_OVERCURRENT]:
                    LOGGER.error("MOTORS OVERCURRENT")
                # Robot DROPPED
                if self.sensor_list[roomba.LEFT_WHEEL_DROP] \
                        or self.sensor_list[roomba.RIGHT_WHEEL_DROP]:
                    LOGGER.error("ROBOT DROPPED")
                    self.status = 'init'
                # Update battery value
                bat_charge = self.sensor_list[roomba.BATTERY_CHARGE] * 1.0
                bat_cap = self.sensor_list[roomba.BATTERY_CAPACITY]
                self.battery = int((bat_charge / bat_cap) * 100)
                # Log Robot position
                if self.status == 'moving' and self.status == 'searching_dock':
                    posx = self.sensor_list[roomba.POS_X]
                    posy = self.sensor_list[roomba.POS_Y]
                    theta = self.sensor_list[roomba.POS_Z]
                    LOGGER.info('ROOMBA POS %f %f %f', posx, posy, theta)

                time.sleep(1)

        return 0
