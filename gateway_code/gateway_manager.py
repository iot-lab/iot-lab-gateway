#! /usr/bin/env python
# -*- coding:utf-8 -*-


"""
manager script
"""

from gateway_code import flash_firmware

class GatewayManager(object):
    """
    Gateway Manager class,

    Manages experiments, open node and control node
    """
    def __init__(self):
        self.exp_id = None
        self.user = None

        self.experiment_is_started = False


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
        self.experiment_is_started = True

        param_str = str((self, exp_id, user, firmware_path, profile))
        ret_str = "%s: %s" % (_unimplemented_fct_str_(), param_str)
        return 0, ret_str


    def exp_stop(self):
        param_str = str((self))
        ret_str = "%s: %s" % (_unimplemented_fct_str_(), param_str)
        return 0, ret_str


    def exp_update_profile(self, profile):
        param_str = str((self, profile))
        ret_str = "%s: %s" % (_unimplemented_fct_str_(), param_str)
        return 0, ret_str



    @staticmethod
    def open_start():
        ret_str = _unimplemented_fct_str_()
        return 0, ret_str

    @staticmethod
    def open_stop():
        ret_str = _unimplemented_fct_str_()
        return 0, ret_str

    @staticmethod
    def open_reset():
        ret_str = _unimplemented_fct_str_()
        return 0, ret_str

    @staticmethod
    def open_flash(firmware_path):
        ret_tuple = flash_firmware.flash('m3', firmware_path)
        return ret_tuple # (ret, out, err)



    @staticmethod
    def control_flash(firmware_path):
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

