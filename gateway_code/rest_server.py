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
from gateway_code import board_config

import logging
LOGGER = logging.getLogger('gateway_code')


class GatewayRest(object):

    """
    Gateway Rest class

    It calls the `gateway_ manager` to handle commands
    """

    def __init__(self, gateway_manager):
        self.gateway_manager = gateway_manager
        self.board_type = board_config.BoardConfig().board_type
        self.board_class = board_config.BoardConfig().board_class
        self._app_routing()

    def _app_routing(self):
        """
        Declare the REST supported methods depending on board config
        """
        # TODO : discuss about option functions
        self.add_route(
            self.exp_start, '/exp/start/<exp_id:int>/<user>', 'POST', 'flash')

        self.add_route(
            self.exp_stop, '/exp/stop', 'DELETE', 'flash')

        self.add_route(
            self.exp_update_profile, '/exp/update', 'POST')

        self.add_route(
            self.open_start, '/open/start', 'PUT')
        
        self.add_route(
            self.open_stop, '/open/stop', 'PUT')

        self.add_route(
            self.status, '/status', 'GET', 'status')

        # query_string: channel=int[11:26]
        self.add_route(
            self.auto_tests, '/autotest', 'PUT', 'flash')

        self.add_route(
            self.auto_tests, '/autotest/<mode>', 'PUT', 'flash')
        # node specific commands
        self.add_route(
            self.open_flash, '/open/flash', 'POST', 'flash')

        self.add_route(
            self.open_soft_reset, '/open/reset', 'PUT', 'reset')

        self.add_route(
            self.open_debug_start, '/open/debug/start', 'PUT', 'debug_start')

        self.add_route(
            self.open_debug_stop, '/open/debug/stop', 'PUT', 'debug_stop')

    def exp_start(self, user, exp_id):
        """
        Start an experiment

        :param user: user of the experiment owner
        :param exp_id: experiment id

        Query string: 'timeout' int
        """

        LOGGER.debug('REST: Start experiment: %s-%i', user, exp_id)
        try:
            timeout = max(0, int(request.query.timeout))
        except ValueError:
            timeout = 0

        # Extract firmware file
        firmware_file = self._extract_firmware()
        firmware = firmware_file.name if firmware_file else None

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
            profile = request.json
            LOGGER.debug('Profile json dict: %r', profile)
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
        firmware_file = NamedTemporaryFile(suffix='--' + _firm.filename)
        firmware_file.write(_firm.file.read())
        firmware_file.flush()
        return firmware_file

    #
    # Open node commands
    #
    def open_flash(self):
        """ Flash open node
        Requires: request.files contains 'firmware' file argument """
        LOGGER.debug('REST: Flash %s', self.board_type)

        firmware_file = self._extract_firmware()
        if firmware_file is None:
            return {'ret': 1, 'error': "Wrong file args: required 'firmware'"}

        ret = self.gateway_manager.node_flash('open', firmware_file.name)

        firmware_file.close()
        return {'ret': ret}

    def open_soft_reset(self):
        """ Soft reset open node """
        LOGGER.debug('REST: Reset %s', self.board_type)
        ret = self.gateway_manager.node_soft_reset('open')
        return {'ret': ret}

    def open_start(self):
        """ Start open node. Alimentation mode stays the same """
        LOGGER.debug('REST: Open node start')
        ret = self.gateway_manager.open_power_start()
        return {'ret': ret}

    def open_stop(self):
        """ Stop open node. Alimentation mode stays the same """
        LOGGER.debug('REST: Open node stop')
        ret = self.gateway_manager.open_power_stop()
        return {'ret': ret}

    def open_debug_start(self):
        """ Start open node debugger """
        LOGGER.debug('REST: Open node debugger start')
        ret = self.gateway_manager.open_debug_start()
        return {'ret': ret}

    def open_debug_stop(self):
        """ Stop open node debugger """
        LOGGER.debug('REST: Open node debugger stop')
        ret = self.gateway_manager.open_debug_stop()
        return {'ret': ret}

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

    def status(self):
        """ Return node status
         * Check nodes ftdi
        """
        LOGGER.debug('REST: status')
        return {'ret': self.gateway_manager.status()}

    def add_route(self, server_function, route_patern, route_type, node_function=None):
        """ if node function exists, the route to server_function is added with the right patern"""

        if node_function is None or hasattr(self.board_class, node_function):
            # just here to prevent a too long condition statement
            if node_function is None or callable(getattr(self.board_class, node_function)):
                bottle.route(route_patern, route_type)(server_function)
                return
        LOGGER.info(
            'Rest Server : The route %s does not exist for this node', route_patern)

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
    parser.add_argument('host', type=str, help="Server address to bind to")
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

    GatewayRest(g_m)
    bottle.run(host=host, port=port, server='paste')
