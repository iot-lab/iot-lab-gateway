#! /usr/bin/env python
# -*- coding:utf-8 -*-

""" Open A8 interface """

import os
import shlex
from subprocess import check_output, check_call
from subprocess import STDOUT, CalledProcessError

from gateway_code.config import static_path
from gateway_code.utils.serial_expect import SerialExpectForSocket


import logging
LOGGER = logging.getLogger('gateway_code')

_SSH_OPTS = '-F {ssh_cfg}'.format(ssh_cfg=static_path('ssh_a8_config'))
SSH_CMD = 'ssh ' + _SSH_OPTS + ' {ip_addr} "source /etc/profile; {cmd}"'
SCP_CMD = 'scp ' + _SSH_OPTS + ' {path} {ip_addr}:{remote_path}'

MAC_CMD = "cat /sys/class/net/eth0/address"
IP_CMD = ("ip addr show dev eth0 " +
          r" | sed -n '/inet/ s/.*inet \([^ ]*\)\/.*/\1/p'")


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

    @staticmethod
    def _get_ip_addr():
        """ Wait until open node is booted and get its ip address"""
        with SerialExpectForSocket(logger=LOGGER) as a8_expect:
            a8_expect.send('root')
            a8_expect.expect('# ')
            a8_expect.send(IP_CMD)
            ip_addr = a8_expect.expect(r'\d+\.\d+\.\d+.\d+', timeout=10)
            a8_expect.send('exit')
            if not ip_addr:  # pragma: no cover
                raise A8ConnectionError("Invalid Ip address", ip_addr)
        return ip_addr

    def start(self):
        """ Start a redirection of open_A8 M3 node serial """

        self.ip_addr = self._get_ip_addr()

        try:
            # Run dummy command to hide warning "adding to list of known host"
            self.ssh_run('echo "ssh ok"')
        except CalledProcessError as err:  # pragma: no cover
            raise A8ConnectionError("OpenA8 ssh failed %s" % str(err),
                                    "open_a8_ssh_connection_failed")

        output = self.ssh_run('touch /tmp/boot_errors; cat /tmp/boot_errors')
        if len(output):  # pragma: no cover
            raise A8ConnectionError("Open A8 FTDI config failed", output)

        # test if config OK for OPEN A8 m3
        output = self.ssh_run('ftdi-devices-list')
        if 'A8-M3' not in output:  # pragma: no cover
            raise A8ConnectionError("Open A8 doesn't have M3 configured",
                                    "Open_A8_m3_ftdi_not_configured")

        self.ssh_run('/etc/init.d/serial_redirection restart')

    def get_mac_addr(self):
        """ Get eth0 mac address """
        mac_addr_s = self.ssh_run(MAC_CMD)
        mac_addr = mac_addr_s.strip()
        return mac_addr

    def flash(self, fw_path, dest='/tmp'):
        """ Flash firmware on open node A8 """
        try:
            fw_remote = os.path.join(dest, os.path.basename(fw_path))
            self.scp(fw_path, fw_remote)
            self.ssh_run('flash_a8_m3 %s' % fw_remote)
            return 0
        except CalledProcessError:
            return 1

    def ssh_run(self, command):
        """ Run SSH command on A8 node """
        cmd = SSH_CMD.format(ip_addr=self.ip_addr, cmd=command)
        LOGGER.debug(cmd)

        output = check_output(shlex.split(cmd), stderr=STDOUT)
        return output

    def scp(self, src, dest):
        """ SCP scr to A8 node at dest """
        cmd = SCP_CMD.format(ip_addr=self.ip_addr, path=src, remote_path=dest)
        LOGGER.debug(cmd)
        check_call(shlex.split(cmd))
