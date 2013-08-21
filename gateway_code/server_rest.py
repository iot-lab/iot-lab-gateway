#-*- coding: utf-8 -*-

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
        bottle.route('/exp/start/:expid/:username', 'POST')(self.exp_start)
        bottle.route('/exp/stop', 'DELETE')(self.exp_stop)
        bottle.route('/open/start', 'PUT')(self.open_start)
        bottle.route('/open/stop', 'PUT')(self.open_stop)

        # node specific commands
        if self.board_type == 'M3':
            bottle.route('/open/flash', 'POST')(self.open_flash)
            bottle.route('/open/reset', 'PUT')(self.open_soft_reset)
        else:  # pragma: no cover
            pass  # handle A8 nodes here

    def exp_start(self, expid, username):
        """
        Start an experiment

        :param expid: experiment id
        :param username: username of the experiment owner
        """
        expid = int(expid)
        LOGGER.info('Start experiment: %s-%i', username, expid)

        firmware_path = None
        firmware_file = None
        profile = None

        # verify passed files as request
        try:
            if 'profile' in request.files:
                # create profile object from json
                _prof = request.files['profile']
                try:
                    profile = json.load(_prof.file)
                except ValueError:
                    LOGGER.error('Invalid json for profile')
                    return {'ret': 1}
            if self.board_type == 'M3' and 'firmware' in request.files:
                # save http file to disk
                _firm = request.files['firmware']
                firmware_file = NamedTemporaryFile(suffix='--'+_firm.filename)
                firmware_path = firmware_file.name
                firmware_file.write(_firm.file.read())
        except ValueError:  # pragma: no cover
            pass  # Detect no files in multipart request

        ret = self.gateway_manager.exp_start(
            expid, username, firmware_path, profile)

        # cleanup of temp file
        if firmware_file is not None:
            firmware_file.close()

        if ret == 0:
            LOGGER.info('Start experiment Succeeded')
        else:  # pragma: no cover
            LOGGER.error('Start experiment with errors: ret: %d', ret)
        return {'ret': ret}

    def exp_stop(self):
        """ Stop the current experiment """
        LOGGER.info('Stop experiment')

        ret = self.gateway_manager.exp_stop()
        if ret == 0:
            LOGGER.info('Stop experiment Succeeded')
        else:  # pragma: no cover
            LOGGER.error('Stop experiment errors: ret: %d', ret)
        return {'ret': ret}

    def reset_time(self):
        """
        Reset Control node time and update time reference
        """
        LOGGER.info('Reset Time')
        ret = self.gateway_manager.reset_time()
        return {'ret': ret}

    def _flash(self, node):
        """
        Flash node

        Requires:
        request.files contains 'firmware' file argument
        """
        ret = 0
        try:
            firmware = request.files['firmware']
        except KeyError:
            return {'ret': 1, 'error': "Wrong file args: required 'firmware'"}
        LOGGER.info("Flash Firmware '%s', on %s",
                    request.files.get('firmware').filename, node)

        # save http file to disk
        with NamedTemporaryFile(suffix='--'+firmware.filename) as _file:
            _file.write(firmware.file.read())
            ret = self.gateway_manager.node_flash(node, _file.name)
        return {'ret': ret}

    def _reset(self, node):
        """ Reset given node with 'reset' pin """
        LOGGER.info("Reset node: %s", node)
        return self.gateway_manager.node_soft_reset(node)

    def open_flash(self):
        """ Flash open node """
        return self._flash('m3')

    def open_soft_reset(self):
        """ Soft reset open node """
        ret = self._reset('m3')
        return {'ret': ret}

    def open_start(self):
        """ Start open node. Alimentation mode stays the same """
        ret = self.gateway_manager.open_power_start(power=None)
        return {'ret': ret}

    def open_stop(self):
        """ Stop open node. Alimentation mode stays the same """
        ret = self.gateway_manager.open_power_stop(power=None)
        return {'ret': ret}

    # Admins commands
    def admin_control_soft_reset(self):
        """ Soft reset control node """
        ret = self._reset('gwt')
        return {'ret': ret}

    def admin_control_flash(self):
        """ Flash control node """
        return self._flash('gwt')


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

    _ = GatewayRest(GatewayManager(log_folder))
    bottle.run(host=host, port=port, server='paste')
