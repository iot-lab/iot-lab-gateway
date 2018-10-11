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


""" Module managing the open node serial redirection """

import os.path
import shlex

import logging

from .external_process import ExternalProcess

LOGGER = logging.getLogger('gateway_code')


class SerialRedirection(ExternalProcess):
    """ Class providing node serial redirection to a tcp socket

    It's implemented as a stoppable thread running socat in a loop.

    Socat is run in a loop instead of using 'tcp-listen,..,fork' because we
    want
    """
    SOCAT = ('socat -d'
             ' TCP4-LISTEN:20000,reuseaddr'
             ' open:{tty},b{baud},echo=0,raw')
    NAME = "serial redirection"

    def __init__(self, tty, baudrate):
        self.tty = tty
        self.process_cmd = shlex.split(self.SOCAT.format(tty=tty,
                                                         baud=baudrate))

        super(SerialRedirection, self).__init__()

    def check_error(self, retcode):
        """Check the return code on exit and print a warning on error."""
        if retcode and self._run:
            if not os.path.exists(self.tty):
                LOGGER.warning('%s: %s not found', self.NAME, self.tty)
        return retcode
