#! /usr/bin/env python
# -*- coding:utf-8 -*-


"""
manager script
"""

from gateway_code import flash_firmware, reset
from gateway_code.serial_redirection import SerialRedirection
import time

import gateway_code.gateway_logging
import logging

LOGGER = logging.getLogger("gateway_logger")

class GatewayManager(object):
    """
    Gateway Manager class,

    Manages experiments, open node and control node
    """
    def __init__(self, log_folder='.'):

        # configure the logger
        gateway_code.gateway_logging.init_logger(log_folder)


        self.exp_id = None
        self.user = None

        self.experiment_is_running = False
        self.current_profile = None

        self.start_experiment_time = None

        self.serial_redirection = None

    def cb_serial_redirection_error(self, handler_arg, error_code):
        """ Callback for SerialRedirection error handler """
        param_str = str((self, handler_arg, error_code))
        ret_str = "%s: %s" % (_unimplemented_fct_str_(), param_str)
        raise  NotImplementedError(0, ret_str)


    def exp_start(self, exp_id, user, firmware_path, profile):
        """
        Start an experiment

        :param exp_id: experiment id
        :param user: user owning the experiment
        :param firmware_path: path of the firmware file to flash
        :param profile: profile to configure the experiment
        :type profile: class Profile

        """

        if self.experiment_is_running:
            ret_dict = {'ret':1, 'err':'Experiment already running'}
            return ret_dict

        self.exp_id = exp_id
        self.user = user
        self.experiment_is_running = True
        self.current_profile = profile
        ret_dict = {}


        # ret = self. set dc power

        ret, err = self.open_power_start()
        ret = 0
        if ret == 0:
            # attente ready
            ret_d = self.open_flash(firmware_path)
            ret_dict['flash_firmware'] = ret_d
            ret = ret_d['ret']

        if ret == 0:
            ret_d = self.exp_update_profile(profile)
            ret_dict['update_profile'] = ret_d

            # REMOVE ME
            err = "NOT_IMPLEMENTED %s" % self.exp_update_profile.__name__
            ret_dict['update_profile']['err'] = err
            ret = ret_d['ret']

        # save the start experiment time
        self.start_experiment_time = time.localtime()
        # set_time_0
        # set control node time to 0


        # start the serial port redirection
        if ret == 0:
            self.serial_redirection = SerialRedirection('m3', \
                    error_handler = self.cb_serial_redirection_error)
            ret = self.serial_redirection.start()
            ret_dict['serial_redirection.start'] = {'ret':ret}


        # start the gdb server

        # reset the open node
        if ret == 0:
            ret_d = self.open_soft_reset()
            ret_dict['reset'] = ret_d
            ret = ret_d['ret']


        return ret_dict


    def exp_stop(self):
        """
        Stop the current running experiment
        """
        if not self.experiment_is_running:
            return {'ret': 1, 'err': 'No experiment running'}


        # stop redirection
        ret = self.serial_redirection.stop()

        # stop gdb server

        # set dc ON
        # flash idle firmware
        #


        # update experiment profile with a
        #   'no polling',
        #   'battery charge',
        #   'power off'
        # profile


        # shut down open node ?

        # reset the manager
        self.__init__()


        param_str = str((self))
        ret_str = "%s: %s" % (_unimplemented_fct_str_(), param_str)
        ret_dict = {'ret':ret, 'err': ret_str, 'out': 'stop redirection'}

        return ret_dict


    def exp_update_profile(self, profile):
        """
        Update the control node profile
        """
        self.current_profile = profile

        # send profile to CN


        ret_dict = {'ret':0, 'out': 'update profile name : %s' % \
                self.current_profile.profilename }

        return ret_dict



    @staticmethod
    def open_power_start():
        """
        Power on the open node
        """
        ret_str = _unimplemented_fct_str_()
        return 0, ret_str

    @staticmethod
    def open_power_stop():
        """
        Power off the open node
        """

        ret_str = _unimplemented_fct_str_()
        return 0, ret_str

    @staticmethod
    def open_soft_reset():
        """
        Reset the open node using the 'reset' pin
        """
        ret, out, err = reset.reset('m3')
        ret_dict = {'ret': ret, 'out': out, 'err': err}
        return ret_dict


    @staticmethod
    def open_flash(firmware_path):
        """
        Flash the given firmware on the open node
        """
        ret, out, err = flash_firmware.flash('m3', firmware_path)
        ret_dict = {'ret': ret, 'out': out, 'err': err}
        return ret_dict


    @staticmethod
    def control_flash(firmware_path):
        """
        Flash the given firmware on the control node

        :note: Admin command
        """
        ret, out, err = flash_firmware.flash('gwt', firmware_path)
        ret_dict = {'ret': ret, 'out': out, 'err': err}
        return ret_dict


def _unimplemented_fct_str_():
    """
    Current function name

    :note: 'current' means the caller
    """
    import sys
    # disable the pylint warning:
    # "Access to a protected member _getframe of a client class"
    # pylint: disable-msg=W0212
    fct = sys._getframe(1).f_code.co_name
    ret_str = "Not implemented %s" % fct
    return ret_str

