#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
REST server listening to the experiment handler
"""

import bottle
from bottle import request
from tempfile import NamedTemporaryFile
import json

from gateway_code.gateway_manager import GatewayManager
from gateway_code import config

import logging
LOGGER = logging.getLogger('gateway_code')


class GatewayRest(object):
    """
    Gateway Rest class

    It calls the `gateway_ manager` to handle commands
    """
    def __init__(self, gateway_manager):
        self.gateway_manager = gateway_manager
        self.board_type = config.board_type()
        self._app_routing()

    def _app_routing(self):
        """
        Declare the REST supported methods depending on board config
        """
        bottle.route('/exp/start/<exp_id:int>/<user>', 'POST')(self.exp_start)
        bottle.route('/exp/stop', 'DELETE')(self.exp_stop)
        bottle.route('/exp/update', 'PUT')(self.exp_update_profile)
        bottle.route('/open/start', 'PUT')(self.open_start)
        bottle.route('/open/stop', 'PUT')(self.open_stop)

        # query_string: channel=int[11:26]
        bottle.route('/autotest', 'PUT')(self.auto_tests)
        bottle.route('/autotest/<mode>', 'PUT')(self.auto_tests)

        # node specific commands
        if self.board_type == 'M3':
            bottle.route('/open/flash', 'POST')(self.open_flash)
            bottle.route('/open/reset', 'PUT')(self.open_soft_reset)
        else:  # pragma: no cover
            pass  # handle A8 nodes here

    def exp_start(self, user, exp_id):
        """
        Start an experiment

        :param user: user of the experiment owner
        :param exp_id: experiment id

        Query string: 'timeout' int
        """

        exp_id = int(exp_id)
        LOGGER.debug('REST: Start experiment: %s-%i', user, exp_id)
        try:
            timeout = max(0, int(request.query.timeout))
        except ValueError:
            timeout = 0

        # Extract firmware file
        firmware_file = self._extract_firmware()
        firmware = firmware_file.name if firmware_file is not None else None

        # Extract profile to a dict
        try:
            profile = self._extract_profile()
        except ValueError:
            LOGGER.error('Invalid json for profile')
            return {'ret': 1}

        ret = self.gateway_manager.exp_start(
            user, exp_id, firmware, profile, timeout)

        # cleanup of temp file
        if firmware_file is not None:
            firmware_file.close()

        if ret:  # pragma: no cover
            LOGGER.error('Start experiment with errors: ret: %d', ret)
        return {'ret': ret}

    def exp_stop(self):
        """ Stop the current experiment """
        LOGGER.debug('REST: Stop experiment')
        ret = self.gateway_manager.exp_stop()
        if ret:  # pragma: no cover
            LOGGER.error('Stop experiment errors: ret: %d', ret)
        return {'ret': ret}

    def exp_update_profile(self):
        """ Update current experiment profile """
        LOGGER.debug('REST: Update profile')
        try:
            profile = self._extract_profile()
        except ValueError:
            LOGGER.error('Invalid json for profile')
            return {'ret': 1}

        ret = self.gateway_manager.exp_update_profile(profile)
        return {'ret': ret}

    @staticmethod
    def _extract_profile():
        """ Extract profile dict from request files
        :raises: ValueError on an invalid pofile """
        try:
            _prof = request.files['profile']
        except (ValueError, KeyError):
            # ValueError: no files in multipart request
            return None

        profile = json.load(_prof.file)  # ValueError on invalid profile
        LOGGER.debug('Profile json dict: %r', profile)
        return profile

    @staticmethod
    def _extract_firmware():
        """ Extract firmware from request files """
        try:
            _firm = request.files['firmware']
        except (ValueError, KeyError):
            # ValueError: no files in multipart request
            return None

        # save http file to disk
        firmware_file = NamedTemporaryFile(suffix='--'+_firm.filename)
        firmware_file.write(_firm.file.read())
        firmware_file.flush()
        return firmware_file

    def set_time(self):
        """ Reset Control node time and update time reference """
        LOGGER.debug('REST: Set time')
        ret = self.gateway_manager.set_time()
        return {'ret': ret}

    def _flash(self, node):
        """
        Flash node

        Requires:
        request.files contains 'firmware' file argument
        """
        ret = 0

        firmware_file = self._extract_firmware()
        if firmware_file is None:
            return {'ret': 1, 'error': "Wrong file args: required 'firmware'"}

        ret = self.gateway_manager.node_flash(node, firmware_file.name)

        firmware_file.close()
        return {'ret': ret}

    def _reset(self, node):
        """ Reset given node with 'reset' pin """
        return self.gateway_manager.node_soft_reset(node)

    def open_flash(self):
        """ Flash open node """
        LOGGER.debug('REST: Flash M3')
        return self._flash('m3')

    def open_soft_reset(self):
        """ Soft reset open node """
        LOGGER.debug('REST: Reset M3')
        ret = self._reset('m3')
        return {'ret': ret}

    def open_start(self):
        """ Start open node. Alimentation mode stays the same """
        LOGGER.debug('REST: Open node start')
        ret = self.gateway_manager.open_power_start(power=None)
        return {'ret': ret}

    def open_stop(self):
        """ Stop open node. Alimentation mode stays the same """
        LOGGER.debug('REST: Open node stop')
        ret = self.gateway_manager.open_power_stop(power=None)
        return {'ret': ret}

    # Admins commands
    def admin_control_soft_reset(self):
        """ Soft reset control node """
        LOGGER.debug('REST: Reset CN')
        ret = self._reset('gwt')
        return {'ret': ret}

    def admin_control_flash(self):
        """ Flash control node """
        LOGGER.debug('REST: Flash CN')
        return self._flash('gwt')

    def auto_tests(self, mode=None):
        """ Run auto-tests

        :param mode: 'blink'
         Query string: 'channel' int 11-26
         Query string: 'gps' int 0-1
         Query string: 'flash' int 0-1

        Mode:
         * 'blink': leds keep blinking
        """
        LOGGER.debug('REST: auto_tests')

        # get mode
        if mode not in ['blink', None]:
            return {'ret': 1, 'success': [], 'errors': ['invalid_mode']}
        blink = (mode == 'blink')

        # query optionnal channel
        # if defined it should be int(11:26)
        channel_str = request.query.channel
        if channel_str == '':
            channel = None
        elif channel_str.isdigit() and int(channel_str) in range(11, 27):
            channel = int(channel_str)
        else:
            return {'ret': 1, 'success': [], 'errors': ['invalid_channel']}

        try:
            gps_str = request.query.gps
            gps = bool(gps_str and int(gps_str))  # check None or int
        except ValueError:
            return {'ret': 1, 'success': [], 'errors': ['invalid_gps_option']}
        try:
            flash_str = request.query.flash
            flash = bool(flash_str and int(flash_str))  # check None or int
        except ValueError:
            return {'ret': 1, 'success': [],
                    'errors': ['invalid_flash_option']}

        ret_dict = self.gateway_manager.auto_tests(channel, blink, flash, gps)
        return ret_dict


#
# Command line functions
#
def _parse_arguments(args):
    """
    Parse arguments:
        [host, port]

    :param args: arguments, without the script name == sys.argv[1:]
    :type args: list
    """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('host', type=str,
                        help="Server address to bind to")
    parser.add_argument('port', type=int, help="Server port to bind to")
    parser.add_argument(
        '--log-folder', default='.',
        help="Folder where to write logs, default current folder")
    arguments = parser.parse_args(args)

    return arguments.host, arguments.port, arguments.log_folder


def _main(args):
    """
    Command line main function
    """

    host, port, log_folder = _parse_arguments(args[1:])

    g_m = GatewayManager(log_folder)
    g_m.setup()

    _ = GatewayRest(g_m)
    bottle.run(host=host, port=port, server='paste')
