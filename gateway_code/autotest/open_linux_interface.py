#! /usr/bin/env python
# -*- coding:utf-8 -*-

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


""" Linux node interface """

import shlex
import logging
from subprocess import check_output, check_call, STDOUT, CalledProcessError

from gateway_code.config import static_path
from gateway_code.utils.serial_expect import SerialExpectForSocket

LOGGER = logging.getLogger('gateway_code')

_SSH_OPTS = '-F {ssh_cfg}'.format(ssh_cfg=static_path('ssh_linux_config'))
SSH_CMD = 'ssh ' + _SSH_OPTS + ' {ip_addr} "source /etc/profile; {cmd}"'
SCP_CMD = 'scp ' + _SSH_OPTS + ' {path} {ip_addr}:{remote_path}'

MAC_CMD = "cat /sys/class/net/eth0/address"
IP_CMD = ("ip addr show dev eth0 " +
          r" | sed -n '/inet/ s/.*inet \([^ ]*\)\/.*/\1/p'")


class LinuxConnectionError(Exception):
    """ FatalError during tests """
    def __init__(self, value, err_msg):
        super().__init__()
        self.value = value
        self.err_msg = err_msg

    def __str__(self):
        return repr(self.value) + ' : ' + repr(self.err_msg)


class OpenLinuxConnection:
    """ Connection to the Linux node, redirect open node serial link """
    def __init__(self):
        self.ip_addr = None
        self.local_tty = None

    @staticmethod
    def _get_ip_addr():
        """ Wait until Linux node is booted and get its ip address"""
        with SerialExpectForSocket(logger=LOGGER) as serial_expect:
            serial_expect.send('root')
            serial_expect.expect('# ')
            serial_expect.send(IP_CMD)
            ip_addr = serial_expect.expect(r'\d+\.\d+\.\d+.\d+', timeout=10)
            serial_expect.send('exit')
            if not ip_addr:  # pragma: no cover
                raise LinuxConnectionError("Invalid Ip address", ip_addr)
        return ip_addr

    def start(self):
        """ Start a redirection of open node serial """

        self.ip_addr = self._get_ip_addr()

        try:
            # Run dummy command to hide warning "adding to list of known host"
            self.ssh_run('echo "ssh ok"')
        except CalledProcessError as err:  # pragma: no cover
            raise LinuxConnectionError("Linux node ssh failed %s" % str(err),
                                       "linux_node_ssh_connection_failed")
        self.ssh_run('/etc/init.d/serial_redirection restart')

    def get_mac_addr(self):
        """ Get eth0 mac address """
        mac_addr_s = self.ssh_run(MAC_CMD)
        return mac_addr_s.strip()

    def flash(self):
        """ Flash firmware on open node """
        try:
            # generic programmer script on the Linux node
            self.ssh_run('FW=autotest iotlab_flash')
            return 0
        except CalledProcessError:
            return 1

    def ssh_run(self, command):
        """ Run SSH command on Linux node """
        cmd = SSH_CMD.format(ip_addr=self.ip_addr, cmd=command)
        LOGGER.debug(cmd)

        output = check_output(shlex.split(cmd), stderr=STDOUT)
        return output.decode()

    def scp(self, src, dest):
        """ SCP scr to Linux node at dest """
        cmd = SCP_CMD.format(ip_addr=self.ip_addr, path=src, remote_path=dest)
        LOGGER.debug(cmd)
        check_call(shlex.split(cmd))
