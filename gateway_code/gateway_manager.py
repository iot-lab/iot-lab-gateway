#! /usr/bin/env python
# -*- coding:utf-8 -*-


"""
manager script
"""

import gateway_code.profile
from gateway_code import config
from gateway_code import flash_firmware, reset
# from gateway_code import dispatch, cn_serial_io, protocol, measures_handler
from gateway_code.serial_redirection import SerialRedirection

from gateway_code import control_node_interface, protocol_cn

# import Queue
import time

import gateway_code.gateway_logging
import logging

import atexit

LOGGER = logging.getLogger('gateway_code')

CONTROL_NODE_FIRMWARE = config.STATIC_FILES_PATH + 'control_node.elf'
IDLE_FIRMWARE         = config.STATIC_FILES_PATH + 'idle.elf'

# Disable: I0011 - 'locally disabling warning'
# too many instance attributes
# pylint:disable=I0011,R0902
class GatewayManager(object):
    """
    Gateway Manager class,

    Manages experiments, open node and control node
    """

    def __init__(self, log_folder='.'):

        # current experiment infos
        self.exp_id                = None
        self.user                  = None
        self.experiment_is_running = False

        self.profile       = None
        self.time_reference        = None

        self.open_node_started     = False

        ret = self.node_flash('gwt', CONTROL_NODE_FIRMWARE)
        if ret != 0: # pragma: no cover
            raise StandardError("Control node flash failed: {ret:%d, '%s')" % \
                    (ret, CONTROL_NODE_FIRMWARE))

        # open node interraction
        self.serial_redirection = SerialRedirection('m3', \
                error_handler = self.cb_serial_redirection_error,
                handler_arg = self)

        # setup control node communication
        # measures_queue  = Queue.Queue(1024)
        # self.dispatcher = dispatch.Dispatch(measures_queue, \
        #         protocol.TYPE_MEASURES_MASK)

        #  self.rxtx    = cn_serial_io.RxTxSerial(self.dispatcher.cb_dispatcher)
        #  self.dispatcher.io_write = self.rxtx.write
        #  self.protocol = protocol.Protocol(self.dispatcher.send_command)
        self.cn_serial = control_node_interface.ControlNodeSerial()
        self.protocol  = protocol_cn.Protocol(self.cn_serial.send_command)

        # self.measure_handler = measures_handler.MeasuresReader(\
        #         decoder        = self.protocol.decode_measure_packet,
        #         measures_queue = measures_queue)

        # configure logger
        gateway_code.gateway_logging.init_logger(log_folder)

        atexit.register(self.exp_stop)



    def exp_start(self, exp_id, user, \
            firmware_path=None, profile=None):
        """
        Start an experiment

        :param exp_id: experiment id
        :param user: user owning the experiment
        :param firmware_path: path of the firmware file to flash
        :param profile: profile to configure the experiment
        :type profile: class Profile


        Experiment start steps
        ======================

        1) Prepare Gateway
            a) Reset control node
            b) Start control node serial communication
            c) Start measures handler (OML thread)
        2) Prepare Open node
            a) Start Open Node DC (stopped before)
            b) Flash open node (flash when started DC)
        3) Prepare Control node
            a) Reset time control node, and update time reference
            b) Configure profile
        4) Finish Open node
            a) Start open node serial redirection
            d) Start GDB server
            c) Final reset of open node
        5) Experiment Started

        """

        if self.experiment_is_running:
            LOGGER.warning('Experiment already running')
            return 1

        self.experiment_is_running = True

        self.exp_id                = exp_id
        self.user                  = user

        # default values
        firmware_path              = firmware_path or IDLE_FIRMWARE
        self.profile               = profile \
                if profile is not None else self.default_profile()


        ret_val = 0

        # start steps described in docstring

        # # # # # # # # # #
        # Prepare Gateway #
        # # # # # # # # # #

        ret      = self.node_soft_reset('gwt')
        ret_val += ret
        # self.rxtx.start()   # ret ?
        # self.measure_handler.start(self.user, self.exp_id)

        time.sleep(1) # wait control node Ready, reajust time later
        self.cn_serial.start()
        time.sleep(1) # wait control node Ready, reajust time later

        # # # # # # # # # # #
        # Prepare Open Node #
        # # # # # # # # # # #

        ret      = self.open_power_start(power='dc')
        ret_val += ret
        ret      = self.node_flash('m3', firmware_path)
        ret_val += ret

        # # # # # # # # # # # # #
        # Prepare Control Node  #
        # # # # # # # # # # # # #

        ret      = self.reset_time()
        ret_val += ret
        ret      = self.exp_update_profile()
        ret_val += ret

        # # # # # # # # # # #
        # Finish Open Node  #
        # # # # # # # # # # #

        ret      = self.serial_redirection.start()
        ret_val += ret
        # start the gdb server
        ret      = self.node_soft_reset('m3')
        ret_val += ret


        return ret_val


    def exp_stop(self):
        """
        Stop the current running experiment



        Experiment stop steps
        ======================

        1) Remove open node access
            a) Stop GDB server
            b) Stop open node serial redirection

        2) Cleanup Control node config and open node
            a) Stop measures Control Node, Configure profile == None
            b) Start Open Node DC (may be running on battery)
            b) Flash Idle open node (when DC)
            c) Shutdown open node (DC)

        3) Cleanup control node interraction
            a) Stop control node serial communication
            b) Stop measures handler (OML thread)
            c) Reset control node (just in case)

        4) Cleanup experiment informations
            a) remove current user
            b) remove expid
            c) Remove current profile
            d) Remove time reference
            e) 'Experiment running' = False

        """
        if not self.experiment_is_running:
            ret = 1
            LOGGER.warning('No experiment running')
            return ret

        ret_val = 0

        # # # # # # # # # # # # # #
        # Remove open node access #
        # # # # # # # # # # # # # #

        # stop gdb server
        ret      = self.serial_redirection.stop()
        ret_val += ret

        # # # # # # # # # # # # # # # # # # # # # # #
        # Cleanup Control node config and open node #
        # # # # # # # # # # # # # # # # # # # # # # #

        ret      = self.exp_update_profile(self.default_profile())
        ret_val += ret
        ret      = self.open_power_start(power='dc')
        ret_val += ret
        ret      = self.node_flash('m3', IDLE_FIRMWARE)
        ret_val += ret
        ret      = self.open_power_stop(power='dc')
        ret_val += ret


        # # # # # # # # # # # # # # # # # # #
        # Cleanup control node interraction #
        # # # # # # # # # # # # # # # # # # #

        # self.rxtx.stop()
        # stop measures handler (oml thread)
        # self.measure_handler.stop()
        self.cn_serial.stop()

        ret      = self.node_soft_reset('gwt')
        ret_val += ret

        self.user                  = None
        self.exp_id                = None
        self.profile               = None
        self.time_reference        = None

        self.experiment_is_running = False

        return ret_val


    @staticmethod
    def cb_serial_redirection_error(handler_arg, error_code): # pragma: no cover
        """ Callback for SerialRedirection error handler """
        LOGGER.error('Serial Redirection process failed "socat: ret == %d"', \
                error_code)
        time.sleep(0.5) # prevent quick loop

    def exp_update_profile(self, profile=None):
        """
        Update the control node profile
        """

        LOGGER.debug('Update profile')
        ret = 0

        if profile is not None:
            self.profile = profile

        ret += self.open_power_start(power=self.profile.power)

        ret += self.protocol.config_consumption(
                self.profile.consumption)
        # Radio

        if ret != 0: # pragma: no cover
            LOGGER.error('Profile update failed')
        return ret


    def reset_time(self):
        """
        Reset control node time and update absolute time reference

        Updating time reference is propagated to measures handler
        """
        #   from datetime import datetime
        LOGGER.debug('Reset control node time')

        # save the start experiment time
        #  new_time = datetime.now()
        #  old_time = self.time_reference

        # protocol will update its time when it gets
        # reset_time_ack from control node
        # must be done before the command is actually executed
        # to be sure it's set before the packet arrives
        # self.protocol.new_time = new_time

        # TODO REMOVE ME when reset_time_ack is in place
        #  self.protocol.time = new_time

        # ret = self.protocol.reset_time('reset_time')
        ret = self.protocol.reset_time()

        # if ret == 0:
        #     self.time_reference = new_time
        # else: # pragma: no cover
        #     LOGGER.error('Reset time failed')

        return ret


    def open_power_start(self, power=None):
        """ Power on the open node """
        LOGGER.debug('Open power start')

        if power is None:
            assert self.profile is not None
            power = self.profile.power


        ret = self.protocol.start_stop('start', power)

        if ret == 0:
            self.open_node_started = True
        else: # pragma: no cover
            LOGGER.error('Open power start failed')
        return ret



    def open_power_stop(self, power=None):
        """ Power off the open node """
        LOGGER.debug('Open power stop')
        ret = 0

        if power is None:
            assert self.profile is not None
            power = self.profile.power

        ret = self.protocol.start_stop('stop', power)

        if ret == 0:
            self.open_node_started = False
        else: # pragma: no cover
            LOGGER.error('Open power stop failed')
        return ret



    @staticmethod
    def node_soft_reset(node):
        """
        Reset the given node using reset pin
        :param node: Node name in {'gwt', 'm3'}
        """
        assert node in ['gwt', 'm3'], "Invalid node name"
        LOGGER.debug('Node %s reset', node)

        ret, _out, _err = reset.reset(node)

        if ret != 0: # pragma: no cover
            LOGGER.error('Node %s reset failed: %d', node, ret)

        return ret


    @staticmethod
    def node_flash(node, firmware_path):
        """
        Flash the given firmware on the given node
        :param node: Node name in {'gwt', 'm3'}
        """
        assert node in ['gwt', 'm3'], "Invalid node name"
        LOGGER.debug('Flash firmware on %s: %s', node, firmware_path)

        ret, _out, _err = flash_firmware.flash(node, firmware_path)

        if ret != 0: # pragma: no cover
            LOGGER.error('Flash firmware failed on %s: %d', node, ret)
        return ret

    @staticmethod
    def default_profile():
        """
        Get the default profile
        """
        import json
        with open(config.STATIC_FILES_PATH + 'default_profile.json') as _prof:
            profile_dict = json.load(_prof)
            def_profile = gateway_code.profile.profile_from_dict(profile_dict)
        return def_profile

