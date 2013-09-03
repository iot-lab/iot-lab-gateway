#! /usr/bin/env python
# -*- coding:utf-8 -*-

"""
Auto tests implementation
"""

import time

from gateway_code import config
from gateway_code import open_node_validation_interface
import logging
LOGGER = logging.getLogger('gateway_code')


class GotError(Exception):
    """ Internal exception """
    def __init__(self, value, message):
        super(GotError, self).__init__()
        self.value = value
        self.message = message


def setup(gateway_manager):
    """ Setup auto_tests """
    g_m = gateway_manager
    ret_val = 0

    # security
    if g_m.experiment_is_running:
        raise GotError(1, 'experiment_is_running')

    # configure Control Node
    ret = g_m.node_soft_reset('gwt')
    ret_val += ret
    g_m.cn_serial.start(_args=['-d'])
    time.sleep(1)
    ret = g_m.open_power_start(power='dc')
    ret_val += ret
    ret = g_m.reset_time()
    ret_val += ret

    # setup open node
    ret = g_m.node_flash('m3', config.FIRMWARES['m3_autotest'])
    ret_val += ret
    on_serial = open_node_validation_interface.OpenNodeSerial()
    time.sleep(1)
    on_serial.start()

    if ret_val != 0:
        raise GotError(ret_val, 'error in setup')

    return on_serial


def teardown(gateway_manager, on_serial):
    """ Cleanup auto_tests """
    g_m = gateway_manager
    ret_val = 0

    # restore
    on_serial.stop()
    ret = g_m.node_flash('m3', config.FIRMWARES['idle'])
    ret_val += ret
    ret = g_m.open_power_stop(power='dc')
    ret_val += ret
    g_m.cn_serial.stop()
    return ret_val


def _validate(ret, errors, message, log_message):
    """ Validate an return and print log if necessary """
    errors += [message] if ret else []
    _ = errors
    if ret:
        LOGGER.error('Autotest: %r: %r', message, log_message)
    return ret


def test_get_time(on_serial, errors):
    """ Tries the 'get_time' command """
    # get_time: ['ACK', 'CURRENT_TIME', '=', '122953', 'tick_32khz']
    answer = on_serial.send_command(['get_time'])

    ret = 0 if (answer[:2] == ['ACK', 'CURRENT_TIME']) else 1
    ret += 0 if answer[3].isdigit() else 1

    ret_val = _validate(ret, errors, 'get_time', answer)
    return ret_val


def test_battery_switch(gateway_manager, on_serial, errors):
    """ test_battery_switch
    Test if changing to battery and back resets open_node
    """
    ret_val = 0

    # save time before test
    answer = on_serial.send_command(['get_time'])
    time_1 = int(answer[3]) if answer[0] == 'ACK' else 0

    # switch to battery and get_time
    ret = gateway_manager.open_power_start(power='battery')
    ret_val += _validate(ret, errors, 'open_power_start', ret)
    answer = on_serial.send_command(['get_time'])
    time_2 = int(answer[3]) if answer[0] == 'ACK' else 0

    #
    # TODO maybe test conso measures
    #

    # switch back to dc and get_time
    ret = gateway_manager.open_power_start(power='dc')
    ret_val += _validate(ret, errors, 'open_power_start', ret)
    answer = on_serial.send_command(['get_time'])
    time_3 = int(answer[3]) if answer[0] == 'ACK' else 0

    # check time increasing => no reboot
    time_increasing = 0 if time_3 > time_2 > time_1 else 1
    ret_val += _validate(time_increasing, errors, 'reboot_when_alim_switch',
                         '%d < %d < %d' % (time_1, time_2, time_3))
    return ret_val


def test_flash(on_serial, errors):
    """
    Test Flash
    """
    answer = on_serial.send_command(['test_flash'])
    ret = 0 if (answer[:2] == ['ACK', 'TST_FLASH']) else 1
    return _validate(ret, errors, 'test_flash', answer)


def test_pressure(on_serial, errors):
    answer = on_serial.send_command(['get_pressure'])
    import sys
    print >> sys.stderr, answer


def run_all_get(on_serial):
    import sys
    for cmd in ( 'get_light', 'get_pressure','get_gyro','get_accelero','get_magneto'):
        print >> sys.stderr, on_serial.send_command([cmd])

#    ['ACK', 'LIGHT', '=', '5.2001953E1', 'lux']
#    ['ACK', 'PRESSURE', '=', '9.944219E2', 'mbar']
#    ['ACK', 'GYRO_ROTATION_SPEED', '=', '1.07625', '1.75', '5.2500002E-2', 'dps']
#    ['ACK', 'ACCELERATION', '=', '3.6E-2', '-1.56E-1', '1.0320001']
#    ['ACK', 'MAGNETO', '=', '4.328358E-2', '6.716418E-2', '-3.880597E-1']



def auto_tests(gateway_manager):
    """
    Run Auto-tests on nodes and gateway using 'gateway_manager'
    """
    ret_val = 0
    errors = []

    try:
        on_serial = setup(gateway_manager)

        ret_val += test_flash(on_serial, errors)
        ret_val += test_get_time(on_serial, errors,)

        run_all_get(on_serial)

        # should be done after some time to get a real offset in time
        ret_val += test_battery_switch(gateway_manager, on_serial, errors)
        ret_val += teardown(gateway_manager, on_serial)
    except GotError as err:
        ret_val += err.value
        errors += [err.message]

    return ret_val, {"error": errors}
