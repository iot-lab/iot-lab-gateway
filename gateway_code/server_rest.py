# -*- coding: utf-8 -*-

from bottle import run, post, request
from gateway_code.gateway_manager import GatewayManager
from tempfile import NamedTemporaryFile

import json


@post('/open/flash')
def open_flash():
    """
    Flash open node

    """
    files_d = request.files
    # verify passed files as request
    if (len(files_d) > 1 or not 'firmware' in files_d):
        return "Wrong file arguments, should be 'firmware' and only one file"

    firmware = files_d['firmware']
    manager = GatewayManager()

    with NamedTemporaryFile(suffix = '--' + firmware.filename) as _file:
        _file.write(firmware.file.read())
        print "Start Open Node flash"
        ret_str = manager.open_flash(_file.name)

    return ret_str

@post('/exp/start/:expid/:username')
def exp_start(expid, username):
    """
    Start an experiment

    :param expid: experiment id
    :param username: username of the experiment owner
    """

    files_d = request.files

    # verify passed files as request
    if set(files_d.keys()) != set(('firmware', 'profile')):
        return "Wrong file arguments, should be 'firmware' and 'profile'"
    firmware = files_d['firmware']
    profile = files_d['profile']
    profile_object = json.load(profile.file)

    manager = GatewayManager()

    with NamedTemporaryFile(suffix = '--' + firmware.filename) as _file:
        _file.write(firmware.file.read())
        ret_str = manager.exp_start(expid, username, _file.name, profile_object)
    return ret_str


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
