#! /usr/bin/env python
# -*- coding: utf-8 -*-

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
REST server listening to the experiment handler
"""

import json
import errno
import logging
import functools
import traceback
from tempfile import NamedTemporaryFile

import bottle
from bottle import request

from gateway_code.gateway_manager import GatewayManager
from gateway_code import board_config

LOGGER = logging.getLogger('gateway_code')


class GatewayRest(bottle.Bottle):

    """
    Gateway Rest class

    It calls the `gateway_ manager` to handle commands
    """

    def __init__(self, gateway_manager):
        super(GatewayRest, self).__init__()
        self.gateway_manager = gateway_manager
        self.board_config = board_config.BoardConfig()
        self._app_routing()

    def _app_routing(self):
        """
        Declare the REST supported methods depending on board config
        """
        # GatewayManager global functions
        self.route('/exp/start/<exp_id:int>/<user>', 'POST', self.exp_start)
        self.route('/exp/stop', 'DELETE', self.exp_stop)
        self.route('/status', 'GET', self.status)

        # Control node functions
        self.route('/exp/update', 'POST', self.exp_update_profile)
        self.cn_conditional_route('open_start', '/open/start', 'PUT',
                                  self.open_start)
        self.cn_conditional_route('open_stop', '/open/stop', 'PUT',
                                  self.open_stop)
        # Autotest functions
        # query_string: channel=int[11:26]
        self.route('/autotest', 'PUT', self.auto_tests)
        self.route('/autotest/<mode>', 'PUT', self.auto_tests)
        # Test function
        self.route('/sleep/<seconds:int>', 'GET', self.sleep)

        # Add open_node functions if available
        self.on_conditional_route('flash', '/open/flash', 'POST',
                                  self.open_flash)
        self.on_conditional_route('flash', '/open/flash/idle', 'PUT',
                                  self.open_flash_idle)
        self.on_conditional_route('reset', '/open/reset', 'PUT',
                                  self.open_soft_reset)
        self.on_conditional_route('debug_start', '/open/debug/start', 'PUT',
                                  self.open_debug_start)
        self.on_conditional_route('debug_stop', '/open/debug/stop', 'PUT',
                                  self.open_debug_stop)

    def exp_start(self, user, exp_id):
        """
        Start an experiment

        :param user: user of the experiment owner
        :param exp_id: experiment id

        Query string: 'timeout' int
        """

        LOGGER.debug('REST: Start experiment: %s-%i', user, exp_id)
        try:
            timeout = int(request.query.timeout)  # pylint:disable=no-member
            timeout = max(0, timeout)

        except ValueError:
            timeout = 0

        # Extract firmware file
        firmware_file = self._extract_firmware()
        firmware = firmware_file.name if firmware_file else None

        # Extract profile to a dict
        try:
            profile = self._extract_profile()
        except ValueError:
            LOGGER.error('REST: Invalid json for profile')
            return {'ret': 1}

        ret = self.gateway_manager.exp_start(user, exp_id, firmware, profile,
                                             timeout)
        # cleanup of temp file
        if firmware_file is not None:
            firmware_file.close()
        if ret:  # pragma: no cover
            LOGGER.error('REST: Start experiment with errors: ret: %d', ret)
        return {'ret': ret}

    def exp_stop(self):
        """ Stop the current experiment """
        LOGGER.debug('REST: Stop experiment')
        ret = self.gateway_manager.exp_stop()
        if ret:  # pragma: no cover
            LOGGER.error('REST: Stop experiment errors: ret: %d', ret)
        return {'ret': ret}

    def exp_update_profile(self):
        """ Update current experiment profile """
        LOGGER.debug('REST: Update profile')
        try:
            profile = request.json
            LOGGER.debug('REST: Profile json dict: %r', profile)
        except ValueError:
            LOGGER.error('REST: Invalid json for profile')
            return {'ret': 1}

        ret = self.gateway_manager.exp_update_profile(profile)
        return {'ret': ret}

    @staticmethod
    def _extract_profile():
        """ Extract profile dict from request files
        :raises: ValueError on an invalid pofile """
        try:
            # Issues with 'request.files'
            # pylint:disable=unsubscriptable-object
            _prof = request.files['profile']
        except (ValueError, KeyError):
            # ValueError: no files in multipart request
            return None

        profile = json.load(_prof.file)  # ValueError on invalid profile
        LOGGER.debug('REST: Profile json dict: %r', profile)
        return profile

    @staticmethod
    def _extract_firmware():
        """ Extract firmware from request files """
        try:
            # Issues with 'request.files'
            # pylint:disable=unsubscriptable-object
            _firm = request.files['firmware']
        except (ValueError, KeyError):
            # ValueError: no files in multipart request
            return None

        # save http file to disk
        firmware_file = NamedTemporaryFile(suffix='--' + _firm.filename)
        firmware_file.write(_firm.file.read())
        firmware_file.flush()
        return firmware_file

    # Open node commands
    def open_flash(self):
        """ Flash open node
        Requires: request.files contains 'firmware' file argument """
        LOGGER.debug('REST: Flash OpenNode')

        firmware_file = self._extract_firmware()
        if firmware_file is None:
            return {'ret': 1, 'error': "Wrong file args: required 'firmware'"}

        ret = self.gateway_manager.node_flash('open', firmware_file.name)

        firmware_file.close()
        return {'ret': ret}

    # Open node commands
    def open_flash_idle(self):
        """Flash open node."""
        LOGGER.debug('REST: Flash Idle OpenNode')
        ret = self.gateway_manager.node_flash('open', None)
        return {'ret': ret}

    def open_soft_reset(self):
        """ Soft reset open node """
        LOGGER.debug('REST: Reset OpenNode')
        ret = self.gateway_manager.node_soft_reset('open')
        return {'ret': ret}

    def open_start(self):
        """ Start open node. Alimentation mode stays the same """
        LOGGER.debug('REST: Start OpenNode')
        ret = self.gateway_manager.open_power_start()
        return {'ret': ret}

    def open_stop(self):
        """ Stop open node. Alimentation mode stays the same """
        LOGGER.debug('REST: Stop OpenNode')
        ret = self.gateway_manager.open_power_stop()
        return {'ret': ret}

    def open_debug_start(self):
        """ Start open node debugger """
        LOGGER.debug('REST: Debug OpenNode')
        ret = self.gateway_manager.open_debug_start()
        return {'ret': ret}

    def open_debug_stop(self):
        """ Stop open node debugger """
        LOGGER.debug('REST: Stop debug OpenNode')
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
        LOGGER.debug('REST: Autotests')

        # get mode
        if mode not in ['blink', None]:
            return {'ret': 1, 'success': [], 'errors': ['invalid_mode']}
        blink = (mode == 'blink')

        # query optionnal channel
        # if defined it should be int(11:26)
        channel_str = request.query.channel  # pylint:disable=no-member
        if channel_str == '':
            channel = None
        elif channel_str.isdigit() and int(channel_str) in range(11, 27):
            channel = int(channel_str)
        else:
            return {'ret': 1, 'success': [], 'errors': ['invalid_channel']}

        try:
            gps_str = request.query.gps  # pylint:disable=no-member
            gps = bool(gps_str and int(gps_str))  # check None or int
        except ValueError:
            return {'ret': 1, 'success': [], 'errors': ['invalid_gps_option']}
        try:
            flash_str = request.query.flash  # pylint:disable=no-member
            flash = bool(flash_str and int(flash_str))  # check None or int
        except ValueError:
            return {'ret': 1, 'success': [],
                    'errors': ['invalid_flash_option']}

        ret_dict = self.gateway_manager.auto_tests(channel, blink, flash, gps)
        return ret_dict

    def sleep(self, seconds):
        """Sleep `seconds` seconds."""
        LOGGER.debug('REST: sleep %d', seconds)
        return {'ret': self.gateway_manager.sleep(seconds)}

    def status(self):
        """ Return node status
         * Check nodes ftdi
        """
        LOGGER.debug('REST: Status')
        return {'ret': self.gateway_manager.status()}

    def on_conditional_route(self, func, path, *route_args, **route_kwargs):
        """Add route if node implements 'func'."""
        return self._cond_route(self.board_config.board_class, func, path,
                                *route_args, **route_kwargs)

    def cn_conditional_route(self, func, path, *route_args, **route_kwargs):
        """Add route if control node implements 'func'."""
        return self._cond_route(self.board_config.cn_class, func, path,
                                *route_args, **route_kwargs)

    def _cond_route(self, obj, func, path, *route_args, **route_kwargs):
        """Add route if `obj.func` exists and is callable."""
        has_fct = callable(getattr(obj, func, None))
        if not has_fct:
            LOGGER.debug('REST: Route %s not available', path)
            return None

        LOGGER.info('REST: Route %s registered', path)
        return self.route(path, *route_args, **route_kwargs)

    def route(self, path, method='GET', callback=None, *args, **kwargs):
        """Add a route but catch some exceptions."""
        # pylint:disable=arguments-differ
        callback = self._cb_wrap(callback)
        return super(GatewayRest, self).route(path, method, callback,
                                              *args, **kwargs)

    @staticmethod
    def _cb_wrap(func):
        """Wrap function to catch EnvironmentError(EWOULDBLOCK)."""
        @functools.wraps(func)
        def _wrapped_f(*args, **kwargs):
            """Wrapped function."""
            try:
                return func(*args, **kwargs)
            except EnvironmentError as err:
                if err.errno == errno.EWOULDBLOCK:
                    LOGGER.error('RestServer: Request would block, abort')
                    bottle.response.status = 503
                    return 'Error: 503 Service Unavailable\n'
                LOGGER.error('RestServer: %r', err)
                raise err
            except:
                # Catch all for debugging
                traceback.print_exc()
                raise
        return _wrapped_f

# Command line functions


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
        '--log-folder', dest='log_folder', default='.',
        help="Folder where to write logs, default current folder")
    parser.add_argument(
        '--log-stdout', dest='log_stdout', action='store_true',
        help="Whether to write logs to stdout, default False")
    parser.add_argument(
        '--reloader', dest='reloader', action='store_true',
        help="Whether to auto-reload the bottle server on source code changes")

    arguments = parser.parse_args(args)

    return arguments


def _main(args):
    """
    Command line main function
    """

    args = _parse_arguments(args[1:])
    g_m = GatewayManager(args.log_folder, args.log_stdout)
    g_m.setup()

    server = GatewayRest(g_m)
    server.run(host=args.host, port=args.port, server='paste',
               reloader=args.reloader)
