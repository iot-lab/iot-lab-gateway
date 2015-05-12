# -*- coding:utf-8 -*-
""" Open Node experiment implementation """

from threading import Thread
import time

import gateway_code.config as config
from gateway_code import openocd_cmd
from gateway_code import common
from gateway_code.utils.serial_redirection import SerialRedirection
from gateway_code.autotest import expect

import logging
LOGGER = logging.getLogger('gateway_code')


class NodeM3(object):
    """ Open node M3 implemenation """
    tty = '/dev/ttyON_M3'
    baudrate = 500000
    openocd_cfg_file = 'iot-lab-m3.cfg'

    def __init__(self):
        self.serial_redirection = SerialRedirection(self.tty, self.baudrate)

    def setup(self, firmware_path):
        """ Flash open node, create serial redirection """
        ret_val = 0
        ret_val += common.wait_tty(self.tty, LOGGER, timeout=1)
        ret_val += self.flash(firmware_path)
        ret_val += self.serial_redirection.start()
        return ret_val

    def teardown(self):
        """ Stop serial redirection and flash idle firmware """
        ret_val = 0
        # cleanup debugger before flashing
        ret_val += self.debug_stop()

        ret_val += self.serial_redirection.stop()
        ret_val += self.flash(config.FIRMWARES['idle'])
        return ret_val

    @staticmethod
    def flash(firmware_path):
        """ Flash the given firmware on M3 node
        :param firmware_path: Path to the firmware to be flashed on `node`.
        """
        LOGGER.debug('Flash firmware on M3: %s', firmware_path)
        return openocd_cmd.flash('m3', firmware_path)

    @staticmethod
    def reset():
        """ Reset the M3 node using jtag """
        LOGGER.info('Reset M3 node')
        return openocd_cmd.reset('m3')

    @staticmethod
    def debug_start():
        """ Start M3 node debugger """
        LOGGER.info('M3 Node debugger start')
        return openocd_cmd.OpenOCD.debug_start('m3')

    @staticmethod
    def debug_stop():   # pylint: disable=no-self-use
        """ Stop M3 node debugger """
        LOGGER.info('M3 Node debugger stop')
        return openocd_cmd.OpenOCD.debug_stop('m3')


class NodeA8(object):
    """ Open node A8 implementation """
    tty = '/dev/ttyON_A8'
    baudrate = 115200

    def __init__(self):
        self._a8_expect = None

    def setup(self, firmware_path):  # pylint: disable=unused-argument
        """ Wait that open nodes tty appears and start A8 boot log """
        # 15 secs was not always enough
        ret = common.wait_tty(self.tty, LOGGER, timeout=20)
        if ret == 0:
            # Timeout 15 minutes for boot (we saw 10minutes boot already)
            self._debug_boot_start(15*60)
        return ret

    def teardown(self):
        """ Stop A8 boot log """
        self._debug_boot_stop()
        return 0

    def _debug_boot_start(self, timeout):
        """ A8 boot debug thread start """
        thr = Thread(target=self._debug_thread, args=(timeout,))
        thr.daemon = True
        thr.start()

    def _debug_thread(self, timeout):
        """ Monitor A8 tty to check if node booted """
        t_start = time.time()
        self._a8_expect = expect.SerialExpect(
            self.tty, self.baudrate, logger=LOGGER)
        match = self._a8_expect.expect(' login: ', timeout=timeout)
        delta_t = time.time() - t_start

        if match != '':
            LOGGER.info("Boot A8 succeeded in time: %ds", delta_t)
        else:
            LOGGER.error("Boot A8 failed in time: %ds", delta_t)

    def _debug_boot_stop(self):
        """ Stop the debug thread """
        try:
            self._a8_expect.serial_fd.close()
        except AttributeError:  # pragma: no cover
            pass
