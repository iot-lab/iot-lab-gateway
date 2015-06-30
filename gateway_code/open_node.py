# -*- coding:utf-8 -*-
""" Open Node experiment implementation """

from threading import Thread
import time

from gateway_code.config import static_path
from gateway_code import common
# TODO Add logs for all open nodes
# from gateway_code.common import logger_call

from gateway_code.utils.ftdi_check import ftdi_check
from gateway_code.utils.openocd import OpenOCD
from gateway_code.utils.avrdude import AvrDude
from gateway_code.utils.serial_expect import SerialExpect
from gateway_code.utils.serial_redirection import SerialRedirection

import logging
LOGGER = logging.getLogger('gateway_code')


class NodeLeonardo(object):

    """ Open node Leonardo implemention """
    TTY = '/dev/ttyON_LEONARDO'
    # The Leonardo node need a special open/close and then appear on a new TTY
    TTY_PROG = '/dev/ttyON_LEONARDO_PROG'
    BAUDRATE = 57600
    AVRDUDE_CFG_FILE = static_path('avrdude.conf')
    FW_IDLE = static_path('Idle.cpp.hex')
    # TODO : create the firmware for autotest
    FW_AUTOTEST = static_path('Idle.cpp.hex')
    ALIM = '5V'

    def __init__(self):
        self.serial_redirection = SerialRedirection(self.TTY, self.BAUDRATE)
        self.avrdude = AvrDude(self.AVRDUDE_CFG_FILE, self.TTY_PROG)

    def setup(self, firmware_path):
        """ Flash open node, create serial redirection """
        ret_val = 0
        # it appears that /dev/ttyON_FOX need some time to be detected

        ret_val += common.wait_tty(self.TTY, LOGGER, timeout=3)
        ret_val += self.flash(firmware_path)
        ret_val += self.serial_redirection.start()
        return ret_val

    def teardown(self):
        """ Stop serial redirection and flash idle firmware """
        ret_val = 0
        ret_val += self.serial_redirection.stop()
        ret_val += common.wait_tty(self.TTY, LOGGER, timeout=10)
        ret_val += self.flash(None)
        return ret_val

    def flash(self, firmware_path=None):
        """ Flash the given firmware on Leonardo node
        :param firmware_path: Path to the firmware to be flashed on `node`.
            If None, flash 'idle' firmware """

        if AvrDude.trigger_bootloader(self.TTY, self.TTY_PROG):
            LOGGER.error("FLASH : Leonardo's jtag port not available")
            return 1

        firmware_path = firmware_path or self.FW_IDLE
        LOGGER.info('Flash firmware on Leonardo: %s', firmware_path)
        return self.avrdude.flash(firmware_path)

    def reset(self):
        """ Reset the Leonardo node using jtag """
        LOGGER.info('Reset Leonardo node')
        return AvrDude.trigger_bootloader(self.TTY, self.TTY_PROG)

    def debug_start(self):
        """ Start Leonardo node debugger """
        LOGGER.info('Leonardo Node debugger start')
        # TODO : DO !
        return 1

    def debug_stop(self):
        """ Stop Leonardo node debugger """
        LOGGER.info('Leonardo Node debugger stop')
        # TODO : DO !
        return 1

    @staticmethod
    def status():
        """ Check Leonardo node status """
        # TODO : DO !
        return 0


class NodeFox(object):

    """ Open node FOX implemention """
    # Contrary to m3 node, fox node need some time to be visible.
    # ALso it may fail for user flash/reset after a node start_dc but don't
    # care!
    TTY = '/dev/ttyON_FOX'
    BAUDRATE = 500000
    OPENOCD_CFG_FILE = static_path('iot-lab-fox.cfg')
    FW_IDLE = static_path('idle_fox.elf')
    FW_AUTOTEST = static_path('fox_autotest.elf')
    ALIM = '5V'

    def __init__(self):
        self.serial_redirection = SerialRedirection(self.TTY, self.BAUDRATE)
        self.openocd = OpenOCD(self.OPENOCD_CFG_FILE)

    def setup(self, firmware_path):
        """ Flash open node, create serial redirection """
        ret_val = 0
        # it appears that /dev/ttyON_FOX need some time to be detected

        # Found 1.333 seconds for timeout, so let some margin
        ret_val += common.wait_tty(self.TTY, LOGGER, timeout=3)
        ret_val += self.flash(firmware_path)
        ret_val += self.serial_redirection.start()
        return ret_val

    def teardown(self):
        """ Stop serial redirection and flash idle firmware """
        ret_val = 0
        # ON may have been stopped at the end of the experiment.
        # And then restarted again in cn teardown.
        # This leads to problem where the TTY disappears and reappears during
        # the first 2 seconds. So let some time if it wants to disappear first.
        time.sleep(2)
        ret_val += common.wait_tty(self.TTY, LOGGER, timeout=3)
        # cleanup debugger before flashing
        ret_val += self.debug_stop()
        ret_val += self.serial_redirection.stop()
        ret_val += self.flash(None)
        return ret_val

    def flash(self, firmware_path=None):
        """ Flash the given firmware on FOX node
        :param firmware_path: Path to the firmware to be flashed on `node`.
            If None, flash 'idle' firmware.
        """
        firmware_path = firmware_path or self.FW_IDLE
        LOGGER.info('Flash firmware on FOX: %s', firmware_path)
        return self.openocd.flash(firmware_path)

    def reset(self):
        """ Reset the FOX node using jtag """
        LOGGER.info('Reset FOX node')
        return self.openocd.reset()

    def debug_start(self):
        """ Start FOX node debugger """
        LOGGER.info('FOX Node debugger start')
        return self.openocd.debug_start()

    def debug_stop(self):
        """ Stop FOX node debugger """
        LOGGER.info('FOX Node debugger stop')
        return self.openocd.debug_stop()

    @staticmethod
    def status():
        """ Check FOX node status """
        # Status is called when open node is not powered
        # So can't check for FTDI
        return 0


class NodeM3(object):

    """ Open node M3 implemenation """
    TTY = '/dev/ttyON_M3'
    BAUDRATE = 500000
    OPENOCD_CFG_FILE = static_path('iot-lab-m3.cfg')
    FW_IDLE = static_path('idle_m3.elf')
    FW_AUTOTEST = static_path('m3_autotest.elf')
    ALIM = '3.3V'

    def __init__(self):
        self.serial_redirection = SerialRedirection(self.TTY, self.BAUDRATE)
        self.openocd = OpenOCD(self.OPENOCD_CFG_FILE)

    def setup(self, firmware_path):
        """ Flash open node, create serial redirection """
        ret_val = 0

        ret_val += common.wait_tty(self.TTY, LOGGER, timeout=1)
        ret_val += self.flash(firmware_path)
        ret_val += self.serial_redirection.start()
        return ret_val

    def teardown(self):
        """ Stop serial redirection and flash idle firmware """
        ret_val = 0
        ret_val += common.wait_tty(self.TTY, LOGGER, timeout=1)
        # cleanup debugger before flashing
        ret_val += self.debug_stop()
        ret_val += self.serial_redirection.stop()
        ret_val += self.flash(None)
        return ret_val

    def flash(self, firmware_path=None):
        """ Flash the given firmware on M3 node
        :param firmware_path: Path to the firmware to be flashed on `node`.
            If None, flash 'idle' firmware.
        """
        firmware_path = firmware_path or self.FW_IDLE
        LOGGER.info('Flash firmware on M3: %s', firmware_path)
        return self.openocd.flash(firmware_path)

    def reset(self):
        """ Reset the M3 node using jtag """
        LOGGER.info('Reset M3 node')
        return self.openocd.reset()

    def debug_start(self):
        """ Start M3 node debugger """
        LOGGER.info('M3 Node debugger start')
        return self.openocd.debug_start()

    def debug_stop(self):
        """ Stop M3 node debugger """
        LOGGER.info('M3 Node debugger stop')
        return self.openocd.debug_stop()

    @staticmethod
    def status():
        """ Check M3 node status """
        return ftdi_check('m3', '2232')


class NodeA8(object):

    """ Open node A8 implementation """
    TTY = '/dev/ttyON_A8'
    BAUDRATE = 115200
    LOCAL_A8_M3_TTY = '/tmp/local_ttyA8_M3'
    A8_M3_TTY = '/dev/ttyA8_M3'
    A8_M3_BAUDRATE = 500000
    A8_M3_FW_AUTOTEST = static_path('a8_autotest.elf')
    ALIM = '5V'

    def __init__(self):
        self._a8_expect = None

    def setup(self, firmware_path):  # pylint: disable=unused-argument
        """ Wait that open nodes tty appears and start A8 boot log """
        # 15 secs was not always enough
        ret = common.wait_tty(self.TTY, LOGGER, timeout=20)
        if ret == 0:
            # Timeout 15 minutes for boot (we saw 10minutes boot already)
            self._debug_boot_start(15 * 60)
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
        try:
            self._a8_expect = SerialExpect(self.TTY, self.BAUDRATE, LOGGER)
            match = self._a8_expect.expect(' login: ', timeout=timeout)
        except OSError:
            # Happend in tests that tty disappeared between the first
            # 'wait_tty' and serial creation (fast start/stop)
            match = ''
        delta_t = time.time() - t_start

        if match != '':
            LOGGER.info("Boot A8 succeeded in time: %ds", delta_t)
        else:
            LOGGER.error("Boot A8 failed in time: %ds", delta_t)
        return match

    def _debug_boot_stop(self):
        """ Stop the debug thread """
        try:
            self._a8_expect.serial_fd.close()
        except AttributeError:  # pragma: no cover
            pass

    @staticmethod
    def status():
        """ Check A8 node status """
        # No check done for the moment
        return 0
