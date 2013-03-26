#-*- coding: utf-8 -*-

"""
Rest server listening to the experiment handler

"""

from bottle import run, request, route
from gateway_code.gateway_manager import GatewayManager
from tempfile import NamedTemporaryFile
from gateway_code.profile import ProfileJSONDecoder
import json

class GatewayRest(object):
    """
    Gateway Rest class  

    It calls the gateway manager to treat commands
    """
    def __init__(self, gateway_manager):
        self.gateway_manager = gateway_manager

    @staticmethod
    def __valid_request(required_files_seq):
        """
        Check the file arguments in the request.

        :param required_files_seq: file arguments required in 'request.files'
        :type required_files_seq:  sequence
        :return: If files match required files
        """
        # compare that the two lists have the same elements
        return set(request.files.keys()) == set(required_files_seq)


    def exp_start(self, expid, username):
        """
        Start an experiment

        :param expid: experiment id
        :param username: username of the experiment owner
        """
        # verify passed files as request
        if not self.__valid_request(('firmware', 'profile')):
            return "Wrong file arguments, should be 'firmware' and 'profile'"

        firmware = request.files['firmware']
        profile  = request.files['profile']
        profile_obj = json.load(profile.file, cls=ProfileJSONDecoder)

        with NamedTemporaryFile(suffix = '--' + firmware.filename) as _file:
            _file.write(firmware.file.read())
            ret_dict = self.gateway_manager.exp_start(expid, username, \
                    _file.name, profile_obj)
        return ret_dict


    def exp_stop(self):
        """
        Stop the current experiment
        """

        # no files required, don't check

        ret_dict = self.gateway_manager.exp_stop()
        return ret_dict


    def open_flash(self):
        """
        Flash open node

        Requires:
        request.files contains 'firmware' file argument

        """
        # verify passed files as request
        if not self.__valid_request(('firmware',)):
            return "Wrong file arguments, should be 'firmware'"
        firmware = request.files['firmware']

        print "Start Open Node flash"
        with NamedTemporaryFile(suffix = '--' + firmware.filename) as _file:
            _file.write(firmware.file.read())
            ret_dict = self.gateway_manager.open_flash(_file.name)

        return ret_dict

    def open_soft_reset(self):
        """
        Reset the open node with 'reset' pin
        """
        ret_dict = self.gateway_manager.open_soft_reset()
        return ret_dict


def parse_arguments(args):
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
    arguments = parser.parse_args(args)

    return arguments.host, arguments.port

def app_routing(app):
    """
    routing configuration
    :param app: default application
    """
    route('/exp/start/:expid/:username', 'POST')(app.exp_start)
    route('/exp/stop', 'DELETE')(app.exp_stop)
    route('/open/flash', 'POST')(app.open_flash)
    route('/open/reset', 'PUT')(app.open_soft_reset)


def main(args):
    """
    Command line main function
    """
    app = GatewayRest(GatewayManager())
    app_routing(app)
    host, port = parse_arguments(args[1:])
    run(host=host, port=port, server='paste')
