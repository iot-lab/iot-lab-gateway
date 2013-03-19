# -*- coding: utf-8 -*-

from bottle import route, run, template, post, request
from gateway_code.gateway_manager import GatewayManager

import json

import os

@post('/open/flash')
def open_flash()
   """
   Flash open node  

   """
   files_d = request.files
   # verify passed files as request
   if (len(files_d) > 1 or not 'firmware' in files_d):
      return "Wrong file arguments, should be 'firmware' and only one file"

   firmware = files_d['firmware'] 

   # write firmware to file
   firmware_path = "/tmp/" + firmware.filename
   with open(firmware_path, 'w') as file:
      file.write(firmware.file.read())

   # start flash open node
   manager = GatewayManager()
   print "Start Open Node flash"
   ret_str = manager.open_flash(firmware_path)

   print "Deleting firmware %s" % firmware_path
   os.remove(firmware_path)

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
    if sorted(files_d.keys()) != sorted(['firmware', 'profile']):
        return "Wrong file arguments, should be 'firmware' and 'profile'"
    firmware = files_d['firmware']
    profile = files_d['profile']


    # write firmware to file
    firmware_path = "/tmp/" + firmware.filename
    with open(firmware_path, 'w') as file:
        file.write(firmware.file.read())


    # unpack profile
    profile_object = json.load(profile.file)


    # start experiment
    manager = GatewayManager()
    print "Starting experiment"
    ret_str = manager.exp_start(expid, username, firmware_path, profile_object)
    print "experiment started"

    print "Deleting firmware %s" % firmware_path
    os.remove(firmware_path)

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
