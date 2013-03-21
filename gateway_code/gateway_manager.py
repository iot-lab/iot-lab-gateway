#! /usr/bin/env python
# -*- coding:utf-8 -*-


"""
manager script
"""

from gateway_code import flash_firmware
from gateway_code.serial_redirection import SerialRedirection
import time

class GatewayManager(object):
    """
    Gateway Manager class,

    Manages experiments, open node and control node
    """
    def __init__(self):
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
        :param firmware_path: path of the firmare file to flash
        :param profile: profile to configure the experiment
        :type profile: class Profile

        """
        self.exp_id = exp_id
        self.user = user
        self.experiment_is_running = True
        self.current_profile = profile

        # maybe call 'directly' the specialized class
        # to get a 'clean' return value not decorated for the rest server
        # ie: replace by real function instead of the gateway_manager method
        #    #ret = self.open_flash(firmware_path)
        #    ret, out, err = flash_firmware.flash('m3', firmware_path)

        # ret = self. set dc power
        ret = self.open_power_start()
        ret = 0
        if ret == 0:
            # attente ready
            #ret = self.open_flash(firmware_path)
            ret, out, err = flash_firmware.flash('m3', firmware_path)

        ret = 0
        if ret == 0:
            ret = self.exp_update_profile(profile)

        # save the start experiment time
        self.start_experiment_time = time.localtime()
        # set_time_0
        # set control node time to 0


        # start the serial port redirection
        ret = 0
        if ret == 0:
            self.serial_redirection = SerialRedirection('m3', \
                    error_handler = self.cb_serial_redirection_error)
        if ret == 0:
            ret = self.serial_redirection.start()


        # start the gdb server

        ret = 0
        if ret == 0:
            ret = self.open_soft_reset()


        param_str = str((self, exp_id, user, firmware_path, profile,))
        ret_str = "%s: %s" % (_unimplemented_fct_str_(), param_str)
        ret_dict = {'ret':ret, 'err': ret_str, 'out': out}
        return ret_dict


    def exp_stop(self):
        """
        Stop the current running experiment
        """
        if self.experiment_is_running:
            ret = self.serial_redirection.stop()

        param_str = str((self))
        ret_str = "%s: %s" % (_unimplemented_fct_str_(), param_str)

        # update experiment profile with a
        #   'no polling',
        #   'battery charge',
        #   'power off'
        # profile

        # reset the manager
        self.__init__()

        ret_dict = {'ret':ret, 'err': ret_str, 'out': 'stop redirection'}
        return ret_dict


    def exp_update_profile(self, profile):
        """
        Update the control node profile
        """
        self.current_profile = profile

        param_str = str((self, profile))
        ret_str = "%s: %s" % (_unimplemented_fct_str_(), param_str)
        return 0, ret_str



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
        ret_str = _unimplemented_fct_str_()
        return 0, ret_str


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
        param_str = str((firmware_path))
        ret_str = "%s: %s" % (_unimplemented_fct_str_(), param_str)
        return 0, ret_str


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

