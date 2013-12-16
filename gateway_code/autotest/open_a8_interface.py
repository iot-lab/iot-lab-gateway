#! /usr/bin/env python
# -*- coding:utf-8 -*-

"""
Open A8 interface
"""
import shlex
import time

from gateway_code import config
from gateway_code.autotest import expect
from subprocess import Popen, PIPE, STDOUT, CalledProcessError

import logging
LOGGER = logging.getLogger('gateway_code')

A8_TTY_PATH = '/tmp/tty_open_a8_m3'

_SSH_OPTS = ('-l root ' +
             '-o ConnectTimeout=5 ' +
             '-o StrictHostKeyChecking=no ')

SSH_CMD = 'ssh ' + _SSH_OPTS + ' {ip_addr} "{cmd}"'
SCP_CMD = 'scp ' + _SSH_OPTS + ' {path} {ip_addr}:{remote_path}'

IP_CMD = ("ip addr show dev eth0 " +
          r" | sed -n '/inet/ s/.*inet \([^ ]*\)\/.*/\1/p'")

SOCAT_CMD = ('/usr/local/bin/socat -d TCP4-LISTEN:{port},reuseaddr ' +
             'open:{tty},b{baudrate},echo=0,raw ')
LOCAL_TTY = ('/usr/local/bin/socat -d tcp4-connect:{ip_addr}:{port} ' +
             ' PTY,link={tty},b{baudrate},echo=0,raw')
MAC_CMD = ('ip link show dev eth0 ' +
           r"| sed -n '/ether/ s/.*ether \(.*\) brd.*/\1/p'")


class A8ConnectionError(Exception):
    """ FatalError during tests """
    def __init__(self, value, err_msg):
        super(A8ConnectionError, self).__init__()
        self.value = value
        self.err_msg = err_msg

    def __str__(self):
        return repr(self.value) + ' : ' + repr(self.err_msg)


class OpenA8Connection(object):
    """ Connection to the Open A8, redirect A8-M3 node serial link """
    def __init__(self):
        self.ip_addr = None
        self.local_tty = None
        self.remote_tty = None

    def wait_boot_and_get_ip_address(self):
        """ Wait until open node is booted and get its ip address"""
        a8_serial = expect.SerialExpect(verbose=True, **config.OPEN_A8_CFG)

        import datetime
        LOGGER.debug("Time before boot %s", datetime.datetime.now())
        # boot timeout 2 minutes (seen 50 seconds for a boot in tests)
        ret = a8_serial.expect(' login: ', timeout=120)
        LOGGER.debug("Time after boot %s", datetime.datetime.now())
        if not ret:
            raise A8ConnectionError("Open node didn't booted: %r" % ret,
                                    'boot_timeout')

        a8_serial.send('root')
        a8_serial.expect('# ')

        a8_serial.send(IP_CMD)
        ip_address = a8_serial.expect(r'\d+\.\d+\.\d+.\d+', timeout=10)
        if not ret:
            raise A8ConnectionError("Invalid Ip address",
                                    "invalid_ip:%r" % ip_address)
        a8_serial.send('exit')

        self.ip_addr = ip_address

    def start(self):
        """ Start a redirection of open_A8 M3 node serial """
        port = 20000
        config_a8 = config.NODES_CFG['a8']

        # wait until boot
        self.wait_boot_and_get_ip_address()

        try:
            output = self.ssh_run('cat /tmp/boot_errors')
        except CalledProcessError:
            pass  # file does not exist, don't care
        else:
            if len(output):
                raise A8ConnectionError("Open A8 FTDI config failed", output)

        # test if config OK for OPEN A8 m3
        output = self.ssh_run('ftdi-devices-list')
        if not 'FITECO A8' in output:
            raise A8ConnectionError("Open A8 doesn't have M3 configured",
                                    "Open_A8_m3_ftdi_not_configured")

        # remote TTY
        socat_cmd = SOCAT_CMD.format(port=port, tty=config_a8['tty'],
                                     baudrate=config_a8['baudrate'])
        remote_tty_cmd = 'pkill socat; ' + socat_cmd
        cmd = SSH_CMD.format(ip_addr=self.ip_addr, cmd=remote_tty_cmd)
        self.remote_tty = Popen(shlex.split(cmd))
        time.sleep(10)

        # local_tty
        local_tty = LOCAL_TTY.format(ip_addr=self.ip_addr,
                                     port=port, tty=A8_TTY_PATH,
                                     baudrate=config_a8['baudrate'])
        self.local_tty = Popen(shlex.split(local_tty))
        time.sleep(2)

        if (self.local_tty.poll() is not None or
                self.remote_tty.poll() is not None):
            self.remote_tty.terminate()
            self.local_tty.terminate()
            raise A8ConnectionError("Socat commands shut down too early",
                                    "socat_terminated")

    def stop(self):
        """ Stop redirection of open_A8 M3 node serial """
        try:
            self.ssh_run('pkill socat')
            time.sleep(1)
            self.remote_tty.wait()
            self.local_tty.wait()
        except CalledProcessError:
            # Open node A8 unreachable
            if self.remote_tty is not None:
                self.remote_tty.terminate()
            if self.local_tty is not None:
                self.local_tty.terminate()

    def get_mac_addr(self):
        """ Get eth0 mac address """
        mac_addr_s = self.ssh_run(MAC_CMD)
        mac_addr = mac_addr_s.strip()
        return mac_addr

    def ssh_run(self, command):
        """ Run SSH command on A8 node """
        cmd = SSH_CMD.format(ip_addr=self.ip_addr, cmd=command)

        process = Popen(shlex.split(cmd), stdout=PIPE, stderr=STDOUT)
        output = process.communicate()[0]
        if 0 != process.returncode:
            raise CalledProcessError(returncode=process.returncode,
                                     cmd=shlex.split(cmd))
        return output
