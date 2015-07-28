# -*- coding:utf-8 -*-
""" Open Node Leonardo experiment implementation """

from gateway_code.config import static_path
from gateway_code import common
from gateway_code.common import logger_call

from gateway_code.utils.avrdude import AvrDude
from gateway_code.utils.serial_redirection import SerialRedirection

import logging
LOGGER = logging.getLogger('gateway_code')


class NodeLeonardo(object):

    """ Open node Leonardo implemention """
    TTY = '/dev/ttyON_LEONARDO'
    # The Leonardo node need a special open/close and then appear on a new TTY
    TTY_PROG = '/dev/ttyON_LEONARDO_PROG'
    # Regular TTY will be restored after 8 seconds
    TTY_RESTORE_TIME = 8 + common.TTY_DETECT_TIME

    BAUDRATE = 9600
    FW_IDLE = static_path('idle_leonardo.elf')
    FW_AUTOTEST = static_path('leonardo_autotest.elf')
    AVRDUDE_CONF = {
        'tty': TTY_PROG,
        'baudrate': 9600,
        'model': 'atmega32u4',
        'programmer': 'avr109',
    }

    ALIM = '5V'

    AUTOTEST_ANSWERS = ['check_get_time',
                        'get_uid']

    def __init__(self):
        self.serial_redirection = SerialRedirection(self.TTY, self.BAUDRATE)
        self.avrdude = AvrDude(self.AVRDUDE_CONF)

    @logger_call("Node Leonardo : Setup of leonardo node")
    def setup(self, firmware_path):
        """ Flash open node, create serial redirection """
        ret_val = 0

        common.wait_no_tty(self.TTY)
        ret_val += common.wait_tty(self.TTY, LOGGER)
        ret_val += self.flash(firmware_path)
        ret_val += self.serial_redirection.start()
        return ret_val

    @logger_call("Node Leonardo : Teardown of leonardo node")
    def teardown(self):
        """ Stop serial redirection and flash idle firmware """
        ret_val = 0

        # ON may have been stopped at the end of the experiment.
        # And then restarted again in cn teardown.
        # This leads to problem where the TTY disappears and reappears during
        # the first 2 seconds. So let some time if it wants to disappear first.
        common.wait_no_tty(self.TTY)
        ret_val += common.wait_tty(self.TTY, LOGGER)
        ret_val += self.serial_redirection.stop()
        ret_val += self.flash(None)
        return ret_val

    @logger_call("Node Leonardo : Flash of leonardo node")
    def flash(self, firmware_path=None):
        """ Flash the given firmware on Leonardo node
        :param firmware_path: Path to the firmware to be flashed on `node`.
            If None, flash 'idle' firmware """
        if AvrDude.trigger_bootloader(self.TTY, self.TTY_PROG, timeout=15):
            LOGGER.error("FLASH : Leonardo's jtag port not available")
            return 1
        ret_val = 0
        firmware_path = firmware_path or self.FW_IDLE
        LOGGER.info('Flash firmware on Leonardo: %s', firmware_path)
        ret_val += self.avrdude.flash(firmware_path)
        ret_val += common.wait_tty(self.TTY, LOGGER, self.TTY_RESTORE_TIME)
        return ret_val

    @logger_call("Node Leonardo : Reset of leonardo node")
    def reset(self):
        """ Reset the Leonardo node using jtag """
        ret_val = 0
        ret_val += AvrDude.trigger_bootloader(self.TTY, self.TTY_PROG)
        ret_val += common.wait_tty(self.TTY, LOGGER, self.TTY_RESTORE_TIME)
        return ret_val

    @staticmethod
    def status():
        """ Check Leonardo node status """
        # It's impossible for us to check the status of the leonardo node
        return 0
