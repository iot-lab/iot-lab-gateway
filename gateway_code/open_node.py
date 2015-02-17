# -*- coding:utf-8 -*-


""" Open Node experiment implementation """
import os
from threading import Thread
import time


import gateway_code.config as config
from gateway_code import common
from gateway_code.serial_redirection import SerialRedirection
from gateway_code.autotest import expect

from gateway_code import gateway_logging
LOGGER = gateway_logging.LOGGER


class NodeM3(object):
    """ Open node M3 implemenation """

    def __init__(self, g_m):
        self.g_m = g_m
        self.serial_redirection = SerialRedirection('m3')

    def setup(self, firmware_path):
        """ Flash open node, create serial redirection """
        ret_val = 0
        ret_val += wait_tty(config.NODES_CFG['m3']['tty'], timeout=1)
        ret_val += self.g_m.node_flash('m3', firmware_path)
        ret_val += self.serial_redirection.start()
        return ret_val

    def teardown(self):
        """ Stop serial redirection and flash idle firmware """
        ret_val = 0
        # cleanup debugger before flashing
        ret_val += self.g_m.open_debug_stop()

        ret_val += self.serial_redirection.stop()
        ret_val += self.g_m.node_flash('m3', config.FIRMWARES['idle'])
        return ret_val


class NodeA8(object):
    """ Open node A8 implementation """

    def __init__(self, g_m):  # pylint: disable=unused-argument
        self._a8_expect = None

    def setup(self, firmware_path):  # pylint: disable=unused-argument
        """ Wait that open nodes tty appears and start A8 boot log """
        # 15 secs was not always enough
        ret = wait_tty(config.OPEN_A8_CFG['tty'], timeout=20)
        if ret == 0:
            # Timeout 15 minutes for boot (we saw 10minutes boot already)
            self._debug_a8_boot_start(15*60, config.OPEN_A8_CFG)
        return ret

    def teardown(self):
        """ Stop A8 boot log """
        self._debug_a8_boot_stop_thread()
        return 0

    def _debug_a8_boot_start(self, timeout, open_a8_cfg):
        """ A8 boot debug thread start """
        a8_debug_thread = Thread(target=self._debug_a8_boot_start_thread,
                                 args=(timeout, open_a8_cfg))
        a8_debug_thread.daemon = True
        a8_debug_thread.start()

    def _debug_a8_boot_start_thread(self, timeout, open_a8_cfg):
        """ Monitor A8 tty to check if node booted """
        t_start = time.time()
        self._a8_expect = expect.SerialExpect(logger=LOGGER, **open_a8_cfg)
        match = self._a8_expect.expect(' login: ', timeout=timeout)
        delta_t = time.time() - t_start

        if match != '':
            LOGGER.info("Boot A8 succeeded in time: %ds", delta_t)
        else:
            LOGGER.error("Boot A8 failed in time: %ds", delta_t)

    def _debug_a8_boot_stop_thread(self):
        """ Stop the debug thread """
        try:
            self._a8_expect.serial_fd.close()
        except AttributeError:  # pragma: no cover
            pass


def wait_tty(dev_tty, timeout=0):
    """ Wait that tty is present """
    if common.wait_cond(timeout, True, os.path.exists, dev_tty):
        return 0
    LOGGER.error('Error Open Node tty not visible: %s', dev_tty)
    return 1
