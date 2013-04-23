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

        # current experiment infos
        self.exp_id                = None
        self.user                  = None
        self.experiment_is_running = False
        self.current_profile       = None
        self.time_reference        = None
        self.serial_redirection    = None
        self.open_node_started     = False

        # don't reconfigure when called from __stop__
        if log_folder is not None:
            # configure logger
            gateway_code.gateway_logging.init_logger(log_folder)



    def exp_start(self, exp_id, user, firmware_path, profile):
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
            c) Start open node serial redirection
            d) Start GDB server
        3) Prepare Control node
            a) Reset time control node, and update time reference
            b) Configure profile
        4) Finish
            a) Final reset of open node
        5) Experiment Started

        """

        if self.experiment_is_running:
            LOGGER.error('Experiment already running')
            return 1

        self.exp_id                = exp_id
        self.user                  = user
        self.experiment_is_running = True
        self.current_profile       = profile

        ret_val = 0

        # start steps described in docstring

        ret      = self.node_soft_reset('gwt')
        ret_val += ret

        # start control node reader/writer
        # start measures Handler

        ret      = self.open_power_start(power='dc')
        ret_val += ret
        ret      = self.node_flash('m3', firmware_path)
        ret_val += ret

        ret      = self.reset_time()
        ret_val += ret
        ret      = self.exp_update_profile(profile)
        ret_val += ret

        ret      = self._open_serial_redirection_start()
        ret_val += ret

        # start the gdb server

        ret      = self.node_soft_reset('m3')
        ret_val += ret

        if ret_val == 0:
            LOGGER.info('Start experiment Succeeded')
        else:
            LOGGER.error('Start experiment with errors: ret_val: %d', ret_val)

        return ret_val


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


    def cb_serial_redirection_error(self, handler_arg, error_code):
        """ Callback for SerialRedirection error handler """
        param_str = str((self, handler_arg, error_code))
        ret_str = "%s: %s" % (_unimplemented_fct_str_(), param_str)
        import sys
        print >> sys.stderr, self.serial_redirection.redirector_thread.out
        print >> sys.stderr, self.serial_redirection.redirector_thread.err
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

    def reset_time(self):
        """
        Reset control node time and update absolute time reference

        Updating time reference is propagated to measures handler
        """
        old_time = self.time_reference
        ret = 0

        # save the start experiment time
        new_time = time.time()
        # reset control node time
        # ret = self.
        LOGGER.warning(_unimplemented_fct_str_())
        if ret == 0:
            self.time_reference = new_time

        # send new time to measures_handler

        if old_time is None:
            LOGGER.info('Start experiment time = %r', self.time_reference)
        else:
            LOGGER.info('New time reference = %r', self.time_reference)
        return ret


    def open_power_start(self, power=None):
        """
        Power on the open node
        """
        ret = 0
        self.open_node_started = True

        if power is None:
            # load power from profile
            pass

        LOGGER.info('Open power start')
        LOGGER.warning(_unimplemented_fct_str_())

        if ret != 0:
            LOGGER.error('Open power start failed')
        return ret

    def open_power_stop(self, power=None):
        """
        Power off the open node
        """

        if power is None:
            # load power from profile
            pass

        self.open_node_started = False

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

