#! /usr/bin/env python
# -*- coding:utf-8 -*-

"""
Open A8 interface
"""
import serial
import re

import shlex
import time

from gateway_code import config
from subprocess import Popen, PIPE, STDOUT
from string import Template  # pylint: disable=W0402

A8_TTY_PATH = '/tmp/tty_open_a8_m3'

# Config: have id_rsa key for open_a8 stored in /var/www/.ssh/


_SSH_OPTS = ('-l root ' +
             '-o StrictHostKeyChecking=no ' +
             '-o UserKnownHostsFile=/tmp/known_hosts')


SSH_CMD = Template('ssh %s ${ip_addr} "${cmd}"' % _SSH_OPTS)
SCP_CMD = Template('scp %s ${path} ${ip_addr}:${remote_path}' % _SSH_OPTS)

IP_ADDR_CMD = r"ip addr show dev eth0 " + \
    r"| sed -n '/inet/ s/.*inet \([^ ]*\)\/.*/\1/p'"

SOCAT_CMD = Template('/usr/local/bin/socat -d ' +
                     'TCP4-LISTEN:${port},reuseaddr ' +
                     'open:${tty},b${baudrate},echo=0,raw ')
LOCAL_TTY = Template('/usr/local/bin/socat -d' +
                     ' tcp4-connect:${ip_addr}:${port} ' +
                     ' PTY,link=${tty},b${baudrate},echo=0,raw')
MAC_CMD = "ip link show dev eth0 " + \
    r"| sed -n '/ether/ s/.*ether \(.*\) brd.*/\1/p'"


class OpenA8Connection(object):
    """ Connection to the Open A8, redirect A8-M3 node serial link """
    def __init__(self):
        self.ip_addr = self._get_ip_address()
        self.local_tty = None
        self.remote_tty = None

    def start(self):
        """ Start a redirection of open_A8 M3 node serial """
        port = 20000
        config_a8 = config.NODES_CFG['a8']

        # remote TTY
        socat_cmd = SOCAT_CMD.substitute(port=port,
                                         tty=config_a8['tty'],
                                         baudrate=config_a8['baudrate'])
        remote_tty_cmd = 'pkill socat; ' + socat_cmd
        cmd = SSH_CMD.substitute(ip_addr=self.ip_addr,
                                 cmd=remote_tty_cmd)
        self.remote_tty = Popen(shlex.split(cmd))
        time.sleep(10)

        # local_tty
        local_tty = LOCAL_TTY.substitute(ip_addr=self.ip_addr, port=port,
                                         tty=A8_TTY_PATH,
                                         baudrate=config_a8['baudrate'])
        self.local_tty = Popen(shlex.split(local_tty))
        time.sleep(2)

        if (self.local_tty.poll() is not None or
                self.remote_tty.poll() is not None):
            self.remote_tty.terminate()
            self.local_tty.terminate()
            raise Exception()

    def stop(self):
        """ Stop redirection of open_A8 M3 node serial """
        self.ssh_run('pkill socat')
        time.sleep(1)
        self.remote_tty.wait()
        self.local_tty.wait()

    @staticmethod
    def _get_ip_address():
        """ Get open node a8 ip address from console """

        a8_serial = serial.Serial(config.OPEN_A8_CFG['tty'],
                                  config.OPEN_A8_CFG['baudrate'],
                                  timeout=0.5)
        # connect and wait for prompt == no newlines printed
        a8_serial.write("root\n")
        for _ in range(0, 10):
            if '' == a8_serial.readline():
                break
        else:
            raise ValueError()

        # get ip address
        a8_serial.write(IP_ADDR_CMD + "\n")
        for _ in range(0, 20):
            ip_address = a8_serial.readline().strip()
            if re.match(r'\d+\.\d+\.\d+.\d+', ip_address):
                break
        else:
            raise ValueError()

        a8_serial.write("exit\n")
        a8_serial.close()
        return ip_address

    def get_mac_addr(self):
        """ Get eth0 mac address """
        mac_addr_s = self.ssh_run(MAC_CMD)
        mac_addr = mac_addr_s.strip()
        return mac_addr

    def ssh_run(self, command):
        """ Run SSH command on A8 node """
        cmd = SSH_CMD.substitute(ip_addr=self.ip_addr,
                                 cmd=command)

        process = Popen(shlex.split(cmd), stdout=PIPE, stderr=STDOUT)
        output = process.communicate()[0]
        return output
