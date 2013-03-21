# -*- coding: utf-8 -*-

"""
Rest server listening to the experiment handler

It calls the gateway manager to treat commands
"""

from bottle import run, post, request
from gateway_code.gateway_manager import GatewayManager
from tempfile import NamedTemporaryFile

import json

MANAGER = GatewayManager()

def _valid_request(required_files_seq):
    """
    Check the file arguments in the request.

    :param required_files_seq: file arguments required in 'request.files'
    :type required_files_seq:  sequence
    :return: If files match required files
    """
    # compare that the two lists have the same elements
    return set(request.files.keys()) == set(required_files_seq)

@post('/exp/start/:expid/:username')
def exp_start(expid, username):
    """
    Start an experiment

    :param expid: experiment id
    :param username: username of the experiment owner
    """
    # verify passed files as request
    if not _valid_request(('firmware', 'profile')):
        return "Wrong file arguments, should be 'firmware' and 'profile'"

    firmware = request.files['firmware']
    profile  = request.files['profile']
    profile_obj = json.load(profile.file)

    with NamedTemporaryFile(suffix = '--' + firmware.filename) as _file:
        _file.write(firmware.file.read())
        ret_tuple = MANAGER.exp_start(expid, username, _file.name, profile_obj)
    return str(ret_tuple)

@post('/open/flash')
def open_flash():
    """
    Flash open node

    Requires:
    request.files contains 'firmware' file argument

    """
    # verify passed files as request
    if not _valid_request(('firmware')):
        return "Wrong file arguments, should be 'firmware'"
    firmware = request.files['firmware']

    print "Start Open Node flash"
    with NamedTemporaryFile(suffix = '--' + firmware.filename) as _file:
        _file.write(firmware.file.read())
        ret_tuple = MANAGER.open_flash(_file.name)

    return str(ret_tuple)


def parse_arguments(args):
    """
    Pars arguments:
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


def main(args):
    """
    Command line main function
    """
    host, port = parse_arguments(args[1:])
    run(host=host, port=port, server='paste')
