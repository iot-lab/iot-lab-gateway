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
    def __init__(self, log_folder=None):

        # configure the logger
        # not reconfigure it when called from __stop__
        if log_folder is not None:
            gateway_code.gateway_logging.init_logger(log_folder)


        self.exp_id = None
        self.user = None

        self.experiment_is_running = False
        self.current_profile = None

        self.start_experiment_time = None

        self.serial_redirection = None




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
            ret = 1
            LOGGER.error('Experiment already running')
            return ret

        self.exp_id = exp_id
        self.user = user
        self.experiment_is_running = True
        self.current_profile = profile

        ret_val = 0


        # reset the control node
        ret = self.node_soft_reset('gwt')
        ret_val += ret



        # start node and flash
        self.open_power_start() # with DC current
        ret_val += ret
        # TODO  wait until node is ready ?
        ret = self.node_flash('m3', firmware_path)
        ret_val += ret



        # ret = self. set dc power
        ret = self.exp_update_profile(profile)
        ret_val += ret


        # save the start experiment time
        self.start_experiment_time = time.time()
        LOGGER.info('Start experiment time = %r', self.start_experiment_time)


        # set_time_0
        # set control node time to 0


        # start the serial port redirection
        ret = self._open_serial_redirection_start()
        ret_val += ret


        # start the gdb server



        # final reset the open node
        ret = self.node_soft_reset('m3')
        ret_val += ret

        LOGGER.info('Start experiment finished: ret_val: %d', ret_val)

        return ret_val



    def cb_serial_redirection_error(self, handler_arg, error_code):
        """ Callback for SerialRedirection error handler """
        param_str = str((self, handler_arg, error_code))
        ret_str = "%s: %s" % (_unimplemented_fct_str_(), param_str)
        import sys
        raise  NotImplementedError(0, ret_str)


    def _open_serial_redirection_start(self):
        """
        Start the serial redirection
        """
        LOGGER.info('Open serial redirection start')
        self.serial_redirection = SerialRedirection('m3', \
                error_handler = self.cb_serial_redirection_error)
        ret = self.serial_redirection.start()
        if ret != 0:
            LOGGER.error('Open serial redirection failed')
        return ret



    def exp_stop(self):
        """
        Stop the current running experiment
        """
        if not self.experiment_is_running:
            ret = 1
            LOGGER.error('No experiment running')
            return ret


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

        LOGGER.warning(_unimplemented_fct_str_() + " implem not comlete")
        return 0



    def exp_update_profile(self, profile):
        """
        Update the control node profile
        """
        self.current_profile = profile

        ret = 0
        LOGGER.info('exp_update_profile')
        LOGGER.warning(_unimplemented_fct_str_())

        if ret != 0:
            LOGGER.error('Open power start failed')

        return ret


    @staticmethod
    def open_power_start():
        """
        Power on the open node
        """
        ret = 0


        LOGGER.info('Open power start')
        LOGGER.warning(_unimplemented_fct_str_())

        if ret != 0:
            LOGGER.error('Open power start failed')
        return ret

    @staticmethod
    def open_power_stop():
        """
        Power off the open node
        """

        LOGGER.warning(_unimplemented_fct_str_())
        return 0

    @staticmethod
    def node_soft_reset(node):
        """
        Reset the given node using reset pin
        :param node: Node name in {'gwt', 'm3'}
        """
        assert node in ['gwt', 'm3'], "Invalid node name"
        LOGGER.info('Node %s reset', node)

        ret, _out, _err = reset.reset(node)

        if ret != 0:
            LOGGER.error('Node %s reset failed: %d', node, ret)

        return ret


    @staticmethod
    def node_flash(node, firmware_path):
        """
        Flash the given firmware on the given node
        :param node: Node name in {'gwt', 'm3'}
        """
        assert node in ['gwt', 'm3'], "Invalid node name"
        LOGGER.info('Flash firmware on %s: %s', node, firmware_path)

        ret, _out, _err = flash_firmware.flash(node, firmware_path)

        if ret != 0:
            LOGGER.error('Flash firmware failed on %s: %d', node, ret)
        return ret


def _unimplemented_fct_str_():
    """
    Current function name

    :note: 'current' means the caller
    """
    import sys
    # disable the pylint warning:
    # "Access to a protected member _getframe of a client class"
    # pylint: disable=W0212
    fct = sys._getframe(1).f_code.co_name
    ret_str = "Not implemented %s" % fct
    return ret_str

