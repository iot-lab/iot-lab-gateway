# -*- coding:utf-8 -*-


""" Open Node experiment implementation """
import os
from threading import Thread


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
        ret_val += self.g_m.node_flash('m3', firmware_path)
        ret_val += self.serial_redirection.start()
        # ret_val += self.gdb_server.start()
        return ret_val

    def teardown(self):
        """ Stop serial redirection and flash idle firmware """
        ret_val = 0
        # ret_val += self.gdb_server.stop()
        ret_val += self.serial_redirection.stop()
        ret_val += self.g_m.node_flash('m3', config.FIRMWARES['idle'])
        return ret_val


class NodeA8(object):
    """ Open node A8 implementation """

    def __init__(self, g_m):
        _ = g_m
        self._a8_expect = None

    def setup(self, firmware_path):
        """ Wait that open nodes tty appears and start A8 boot log """
        _ = firmware_path
        # 15 secs was not always enough
        ret = self.wait_tty_a8(config.OPEN_A8_CFG['tty'], timeout=20)
        if ret == 0:
            # Timeout 5 minutes for boot
            self._debug_a8_boot_start(5*60, config.OPEN_A8_CFG)
        return ret

    def teardown(self):
        """ Stop A8 boot log """
        self._debug_a8_boot_stop_thread()
        return 0

    @staticmethod
    def wait_tty_a8(a8_tty, timeout=0):
        """ Procedure to call at a8 startup
        It runs sanity checks and start debug features """
        # Test if open a8 tty correctly appeared
        if common.wait_cond(timeout, True, os.path.exists, a8_tty):
            return 0
        LOGGER.error('Error Open A8 tty not visible: %s', a8_tty)
        return 1

    def _debug_a8_boot_start(self, timeout, open_a8_cfg):
        """ A8 boot debug thread start """
        a8_debug_thread = Thread(target=self._debug_a8_boot_start_thread,
                                 args=(timeout, open_a8_cfg))
        a8_debug_thread.daemon = True
        a8_debug_thread.start()

    def _debug_a8_boot_start_thread(self, timeout, open_a8_cfg):
        """ Monitor A8 tty to check if node booted """
        self._a8_expect = expect.SerialExpect(logger=LOGGER, **open_a8_cfg)
        ret = self._a8_expect.expect(' login: ', timeout=timeout)

        if ret == 0:
            LOGGER.info("Boot A8 succeeded in time: %ds", timeout)
        else:
            LOGGER.error("Boot A8 failed in time: %ds", timeout)

    def _debug_a8_boot_stop_thread(self):
        """ Stop the debug thread """
        try:
            self._a8_expect.serial_fd.close()
        except AttributeError:
            pass
