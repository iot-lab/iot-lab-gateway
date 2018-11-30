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

""" common code for flash/debug tools """

import logging
import os
import shlex
import tempfile

from gateway_code.utils import subprocess_timeout

LOGGER = logging.getLogger('gateway_code')


class FlashTool(object):
    """ common class for flash/debug tools """
    TIMEOUT = 100

    def __init__(self, verb=False, timeout=TIMEOUT):
        self.verb = verb
        self.timeout = timeout
        self.name = self.__class__.__name__

    def args(self, command_str):  # pylint:disable=no-self-use
        """splits a command into arguments for Popen"""

        args = shlex.split(command_str)
        return {'args': args}

    def call_cmd(self, command_str):
        """ Run the given command_str."""

        kwargs = self.args(command_str)

        file_descriptor, temp_path = tempfile.mkstemp()

        LOGGER.info(kwargs)

        temp = open(temp_path, mode='w+')
        kwargs['stdout'] = temp
        kwargs['stderr'] = temp

        try:
            returncode = subprocess_timeout.call(
                timeout=self.timeout, **kwargs)

            temp.seek(0)
            output = temp.read()
            if returncode != 0:
                LOGGER.error(output)
            if self.verb:
                LOGGER.info(output)
            return returncode
        except subprocess_timeout.TimeoutExpired as exc:
            LOGGER.error("%s '%s' timeout: %s", self.name, command_str, exc)
            temp.seek(0)
            output = temp.read()
            LOGGER.error('stdout & stderr')
            LOGGER.error(output)
            return 1
        finally:
            # cleanup
            temp.close()
            os.close(file_descriptor)
            os.remove(temp_path)
