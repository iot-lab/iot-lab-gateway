#! /usr/bin/env python
# -*- coding:utf-8 -*-

""" auto tests implementation """

import time
import bisect

from subprocess import Popen, PIPE, STDOUT, CalledProcessError
from serial import SerialException

# config should be accessed through gateway_code to allow testing...
import gateway_code
from gateway_code.autotest import m3_node_interface
from gateway_code.autotest import open_a8_interface
from gateway_code.profile import Consumption, Radio

import logging
LOGGER = logging.getLogger('gateway_code')

MAC_CMD = "ip link show dev eth0 " + \
    r"| sed -n '/ether/ s/.*ether \(.*\) brd.*/\1/p'"


class FatalError(Exception):
    """ FatalError during tests """
    def __init__(self, value):
        super(FatalError, self).__init__()
        self.value = value

    def __str__(self):
        return repr(self.value)

TST_OK = lambda bool_value: (0 if bool_value else 1)


class AutoTestManager(object):
    """ Gateway and open node auto tests """
    def __init__(self, gateway_manager):
        self.g_m = gateway_manager

        self.on_serial = None
        self.a8_connection = None

        self.ret_dict = None

        self.cn_measures = []

    def _measures_handler(self, measure_str):
        """ control node measures Handler """
        self.cn_measures.append(measure_str.split(' '))

    @staticmethod
    def get_local_mac_addr():
        """ Get eth0 mac address """
        process = Popen(MAC_CMD, stdout=PIPE, stderr=STDOUT, shell=True)
        mac_addr = process.communicate()[0].strip()
        return mac_addr

    def setup_control_node(self):
        """ setup connection with control_node"""

        self.ret_dict = {'ret': None, 'success': [], 'error': [], 'mac': {}}
        ret_val = 0
        LOGGER.info("Setup autotests")

        # configure Control Node
        ret_val += self.g_m.node_soft_reset('gwt')
        self.g_m.cn_serial.start(_measures_handler=self._measures_handler,
                                 _args=['-d'])
        time.sleep(1)

        ret_val += self.g_m.reset_time()

        gwt_mac_addr = self.get_local_mac_addr()
        self.ret_dict['mac']['GWT'] = gwt_mac_addr

        ret_val = self._check(ret_val, 'setup_cn_connection', ret_val)
        if 0 != ret_val:
            raise FatalError('Setup control node failed')

    def _setup_open_node_connection(self):
        """ Setup the connection with Open Node
        Should be done on DC"""

        ret_val = 0
        ret_val += self.g_m.open_power_start(power='dc')
        time.sleep(2)  # wait open node ready

        board_type = gateway_code.config.board_type()
        # setup open node
        if board_type == 'M3':
            ret = self.g_m.node_flash(
                'm3', gateway_code.config.FIRMWARES['m3_autotest'])
            ret_val += self._check(ret, 'flash_m3', ret)
            time.sleep(2)

            self.on_serial = m3_node_interface.OpenNodeSerial()
            ret, err_msg = self.on_serial.start()
            ret_val += self._check(ret, 'open_M3_serial', err_msg)

        elif board_type == 'A8':
            try:
                # wait nodes booting
                self.a8_connection = open_a8_interface.OpenA8Connection()

                # wait nodes start
                # get ip address using serial
                # run socats commands
                LOGGER.debug("Wait that open A8 node starts")
                self.a8_connection.start()

            except SerialException as err:
                ret_val += self._check(1, 'access_A8_serial_port', str(err))
                raise FatalError('Setup Open Node failed')
            except open_a8_interface.A8ConnectionError as err:
                ret_val += self._check(1, 'error_in_open_a8_init: %s' %
                                       err.err_msg, str(err))
                raise FatalError('Setup Open Node failed')

            # save mac address
            self.ret_dict['mac']['A8'] = self.a8_connection.get_mac_addr()

            # open A8 flash
            try:
                self.a8_connection.scp(
                    gateway_code.config.FIRMWARES['a8_autotest'],
                    '/tmp/a8_autotest.elf')
            except CalledProcessError as err:
                ret_val += self._check(1, 'scp a8_autotest.elf fail', str(err))
                raise FatalError('Setup Open Node failed')

            try:
                self.a8_connection.ssh_run(
                    'source /etc/profile; ' +
                    '/usr/bin/flash_a8.sh /tmp/a8_autotest.elf')
            except CalledProcessError as err:
                ret_val += self._check(1, 'Flash A8-M3 fail', str(err))
                raise FatalError('Setup Open Node failed')

            time.sleep(5)
            self.on_serial = m3_node_interface.OpenNodeSerial()
            time.sleep(1)
            ret, err_msg = self.on_serial.start(
                tty=open_a8_interface.A8_TTY_PATH)
            ret_val += self._check(ret, 'open_A8_serial', err_msg)

        if 0 != ret_val:
            raise FatalError('Setup Open Node failed')

    def teardown(self, blink):
        """ cleanup """
        ret_val = 0
        LOGGER.info("Teardown autotests")

        # ensure DC alim
        ret_val += self.g_m.open_power_start(power='dc')

        try:
            self.on_serial.stop()
        except AttributeError:  # access attribute on NoneType
            ret_val += 1
        finally:
            self.on_serial = None

        if not blink:
            LOGGER.debug("Stop open node, no blinking")
            ret_val += self.g_m.open_power_stop(power='dc')
        else:
            LOGGER.debug("Set status on LEDs")

        self.g_m.cn_serial.stop()
        LOGGER.debug("cn_serial stopped")

        if self.a8_connection is not None:
            self.a8_connection.stop()
            LOGGER.debug("a8_connection_stopped")

        return self._check(ret_val, 'teardown', ret_val)

    def auto_tests(self, channel=None, blink=False, flash=False, gps=False):
        """
        run auto-tests on nodes and gateway using 'gateway_manager'
        """
        ret_val = 0
        board_type = gateway_code.config.board_type()
        is_m3 = 'M3' == board_type

        try:
            self.setup_control_node()

            if board_type not in ['M3', 'A8']:
                ret_val += self._check(1, 'board_type: %s' % board_type,
                                       'unkown type')
                raise FatalError('Unkown board_type')

            #
            # Tests using Battery
            #
            # dc -> battery: A8 reboot
            # battery -> dc: No reboot
            # A8 may not work with new batteries (not enough power)
            # so check battery and then switch to DC
            ret_val += self.test_consumption_batt(board_type)

            # switch to DN and configure open node
            self._setup_open_node_connection()
            self.check_get_time()
            self.get_uid()

            #
            # Other tests, run on DC
            #
            ret = self.g_m.open_power_start(power='dc')
            ret_val += self._check(ret, 'switch_to_dc', ret)

            # test IMU
            ret_val += self.test_gyro()
            ret_val += self.test_magneto()
            ret_val += self.test_accelero()

            # test M3-ON communication
            ret_val += self.test_gpio()
            ret_val += self.test_i2c()
            if channel is not None:  # radio tests
                ret_val += self.test_radio_ping_pong(channel)
                ret_val += self.test_radio_with_rssi(channel)

            # test consumption measures
            ret_val += self.test_consumption_dc()

            # M3 specific tests
            if is_m3:
                # cannot test this with A8 I think
                ret_val += self.test_leds_with_consumption()
                # test m3 specific sensors
                ret_val += self.test_pressure()
                ret_val += self.test_light()
                if flash:
                    ret_val += self.test_flash()
            if gps:
                ret_val += self.test_gps()

            # set_leds
            _ = self.on_serial.send_command(['leds_off', '7'])
            if ret_val == 0:
                _ = self.on_serial.send_command(['leds_blink', '7', '500'])
                _ = self.g_m.protocol.green_led_blink()
            else:  # pragma: no cover
                pass
        except FatalError as err:
            # Fatal Error during test, don't run further tests
            LOGGER.error("Fatal Error in tests, stop further tests: %s",
                         str(err))
            ret_val += 1

        # shutdown node if test failed
        ret_val += self.teardown(blink and (ret_val == 0))
        self.ret_dict['ret'] = ret_val

        return self.ret_dict

    def _check(self, ret, operation, log_message=''):
        """ Check the operation
        Adds `operation` to ret_dict in the correct failed or success entry

        :param ret: 0 means success non zero means failure
        :return: 0 if `ret` == 0, a positive value otherwise
        """
        if 0 == int(ret):
            self.ret_dict['success'].append(operation)
            LOGGER.debug('autotest: %r OK: %r', operation, log_message)
        else:
            self.ret_dict['error'].append(operation)
            LOGGER.error('Autotest: %r: %r', operation, log_message)
        return abs(int(ret))

    def _run_test(self, num, cmd, answer_start, parse_function):
        """ Run a test 'num' times.
        In case of success parse answer with 'parse_function' """
        values = []
        for _ in range(0, num):
            answer = self.on_serial.send_command(cmd)
            if (answer is None) or (answer[0:2] != ['ACK', answer_start]):
                LOGGER.debug('%s answer == %r', cmd[0], answer)
            else:
                values.append(parse_function(answer))
        return values

#
# Test implementation
#

    def check_get_time(self):
        """ runs the 'get_time' command
        Error on this check are fatal
        """
        # get_time: ['ACK', 'CURRENT_TIME', '=', '122953', 'tick_32khz']
        answer = self.on_serial.send_command(['get_time'])

        values = self._run_test(5, ['get_time'], 'CURRENT_TIME',
                                (lambda x: x[3].isdigit()))
        test_ok = (any(values))
        ret_val = self._check(TST_OK(test_ok), 'm3_comm_with_get_time', answer)

        if 0 != ret_val:  # fatal Error
            raise FatalError("get_time failed. Can't communicate with M3 node")

    def get_uid(self):
        """ runs the 'get_uid' command
        And add the resulting UID to the global return dictionary
        """
        # get_uid: ['ACK', 'UID', '=', '05D8FF323632483343037109']
        values = self._run_test(1, ['get_uid'], 'UID', (lambda x: x[3]))
        test_ok = len(values)

        if test_ok:
            uid_str = values[0]
            # UID: split every 4 char
            uid_split = [''.join(x) for x in zip(*[iter(uid_str)]*4)]
            uid = ':'.join(uid_split)
            self.ret_dict['open_node_m3_uid'] = uid

        ret_val = self._check(TST_OK(test_ok), 'get_uid', values)
        return ret_val
#
# sensors and flash
#

    def test_flash(self):
        """ test Flash """
        values = self._run_test(1, ['test_flash'], 'TST_FLASH', (lambda x: x))
        test_ok = len(values)
        return self._check(TST_OK(test_ok), 'test_flash', values)

    def test_pressure(self):
        """ test pressure sensor """
        # ['ack', 'PRESSURE', '=', '9.944219E2', 'mbar']
        values = self._run_test(10, ['get_pressure'], 'PRESSURE',
                                (lambda x: float(x[3])))
        test_ok = 1 < len(set(values))
        return self._check(TST_OK(test_ok), 'test_pressure', values)

    def test_light(self):
        """ test light sensor with leds"""
        # ['ACK', 'LIGHT', '=', '5.2001953E1', 'lux']

        # get light with leds
        _ = self.on_serial.send_command(['leds_on', '7'])
        values_on = self._run_test(5, ['get_light'], 'LIGHT',
                                   (lambda x: float(x[3])))
        # get light without leds
        _ = self.on_serial.send_command(['leds_off', '7'])
        values_off = self._run_test(5, ['get_light'], 'LIGHT',
                                    (lambda x: float(x[3])))
        values = values_on + values_off
        test_ok = 1 < len(set(values))

        # if len(set(values)) == 1 and values[0] < 0.20:
        #     # test fails when run with low light, like at night
        #     # so hack to let it work
        #     LOGGER.warning("Got the same value which is '%f'", values[0])
        #     self.ret_dict['warning'] = {'get_light_value': values[0]}
        #     test_ok = False
        return self._check(TST_OK(test_ok), 'get_light', values)

#
# Test GPS
#
    def _test_gps_serial(self):
        """ Test the gps via serial port """
        # TODO Roger
        # wait that GPS is ready or timeout
        time.sleep(60)
        ret = 0
        ret_val = self._check(ret, 'wait_gps_serial', "TODO TODO")
        return ret_val

    def _test_pps_open_node(self):
        """ Test the pps on open A8 m3 node"""
        ret_val = 0

        # start pps on open node
        answer = self.on_serial.send_command(['test_pps_start'])
        if (answer is None) or (answer[:2] != ['ACK', 'GPS_PPS_START']):
            return self._check(1, 'test_pps_start', answer[:2])

        # try to get pps for max 2 min
        end_time = time.time() + 120.0
        while time.time() < end_time:
            time.sleep(5)
            answer = self.on_serial.send_command(['test_pps_get'])
            if (answer is None) or (answer[:2] != ['ACK', 'GPS_PPS_GET']):
                return self._check(1, 'test_pps_get', answer)

            # get pps value
            pps_count = int(answer[3])
            if pps_count > 2:
                ret_val = self._check(0, 'test_pps_open_node', pps_count)
                break
        else:
            ret_val = self._check(1, 'test_pps_open_node_timeout', pps_count)

        _ = self.on_serial.send_command(['test_pps_stop'])
        return ret_val

    def test_gps(self):
        """ Test the gps """
        ret_val = 0
        # ret_val += self._test_gps_serial()
        ret_val += self._test_pps_open_node()
        ret_val = self._check(ret_val, 'test_gps', ret_val)
        return ret_val

#
# Control Node <--> Open Node Interraction
#
    def test_gpio(self):
        """ test GPIO connections """
        ret_val = 0
        # setup control node
        ret_val += self.g_m.protocol.send_cmd(['test_gpio', 'start'])

        values = self._run_test(5, ['test_gpio'], 'GPIO', (lambda x: 0))
        test_ok = len(values)
        ret_val += self._check(TST_OK(test_ok), 'test_gpio_ON-CN', len(values))

        # cleanup
        ret_val += self.g_m.protocol.send_cmd(['test_gpio', 'stop'])
        return ret_val

    def test_i2c(self):
        """ test i2c communication """
        ret_val = 0
        # setup control node
        ret_val += self.g_m.protocol.send_cmd(['test_i2c', 'start'])

        values = self._run_test(1, ['test_i2c'], 'I2C2_CN', (lambda x: x))
        test_ok = len(values)
        ret_val += self._check(TST_OK(test_ok), 'test_i2c_ON<->CN', values)

        # cleanup
        ret_val += self.g_m.protocol.send_cmd(['test_i2c', 'stop'])

        return ret_val

#
# Inertial Measurement Unit
#
    def test_magneto(self):
        """ test magneto sensor """
        # ['ack', 'MAGNETO', '=', '4.328358E-2', '6.716418E-2', '-3.880597E-1']

        values = self._run_test(
            10, ['get_magneto'], 'MAGNETO',
            (lambda x: tuple([float(val) for val in x[3:6]])))

        test_ok = 1 < len(set(values))  # got different values
        return self._check(TST_OK(test_ok), 'get_magneto', values)

    def test_gyro(self):
        """ test gyro sensor """
        # ['ack', 'GYRO_ROTATION_SPEED', '=',
        #  '1.07625', '1.75', '5.2500002E-2', 'dps']

        values = self._run_test(
            10, ['get_gyro'], 'GYRO_ROTATION_SPEED',
            (lambda x: tuple([float(val) for val in x[3:6]])))

        test_ok = 1 < len(set(values))  # got different values
        return self._check(TST_OK(test_ok), 'get_gyro', values)

    def test_accelero(self):
        """ test accelerator sensor """
        # ['ack', 'ACCELERATION', '=', '3.6E-2', '-1.56E-1', '1.0320001']

        values = self._run_test(
            10, ['get_accelero'], 'ACCELERATION',
            (lambda x: tuple([float(val) for val in x[3:6]])))

        test_ok = 1 < len(set(values))  # got different values
        return self._check(TST_OK(test_ok), 'get_accelero', values)

#
# Radio tests
#

    def test_radio_ping_pong(self, channel):
        """ test Radio Ping-pong with control-node """
        ret_val = 0

        # setup control node
        cmd = ['test_radio_ping_pong', 'start', str(channel), '3.0']
        ret_val += self.g_m.protocol.send_cmd(cmd)

        # send 10 packets
        cmd_on = ['radio_ping_pong', '3dBm', str(channel)]
        values = self._run_test(10, cmd_on, 'RADIO_PINGPONG', (lambda x: 0))

        # got at least one answer from control_node
        test_ok = (0 in values)  # at least one success
        ret_val += self._check(TST_OK(test_ok), 'radio_ping_pong', values)

        # cleanup
        ret = self.g_m.protocol.send_cmd(['test_radio_ping_pong', 'stop'])
        ret_val += self._check(ret, 'radio_ping_pong_cleanup', 'cleanup error')
        return ret_val

    def test_radio_with_rssi(self, channel):
        """ Test radio with rssi"""

        # pkt length = 125
        # one measure every ~0.01 seconds
        ret_val = 0
        radio = Radio("rssi", [channel], period=10, num_per_channel=0)
        cmd_on = ['radio_pkt', '3dBm', str(channel)]
        del self.cn_measures[:]

        # get RSSI while sending 10 packets length 125
        ret_val += self.g_m.protocol.config_radio(radio)
        for _ in range(0, 10):
            _ = self.on_serial.send_command(cmd_on)
            time.sleep(0.5)
        ret_val += self.g_m.protocol.config_radio(None)

        # ['measures_debug:', 'radio_measure',
        #      '1378466517.186216', '11', '-91']
        # -91 == no radio detected
        values = [int(measure[4]) for measure in self.cn_measures] + [-91]

        # check that values other than -91 measured
        test_ok = 1 < len(set(values))
        ret_val += self._check(TST_OK(test_ok), 'rssi_measures', set(values))

        return ret_val

#
# Consumption tests
#

    def test_consumption_dc(self):
        """ Try consumption for DC """

        ret_val = 0

        # one measure every ~0.1 seconds

        conso = Consumption(power_source='dc',
                            board_type=gateway_code.config.board_type(),
                            period='1100', average='64',
                            power=True, voltage=True, current=True)
        ret_val += self.g_m.open_power_start(power='dc')

        del self.cn_measures[:]
        # store 2 secs of measures
        ret_val += self.g_m.protocol.config_consumption(conso)
        time.sleep(2)  # get measures for 2 seconds
        ret_val += self.g_m.protocol.config_consumption(None)

        values = []
        # measures_debug: consumption_measure
        #     1378387028.906210 0.257343 3.216250 0.080003
        for measure in self.cn_measures:
            if measure[1] == 'consumption_measure':
                values.append(tuple([float(meas) for meas in measure[3:6]]))

        # TODO Validate value ranges (maybe with idle firmware)

        test_ok = 1 < len(set(values))
        ret_val += self._check(TST_OK(test_ok), 'consumption_dc', values)

        return ret_val

    def test_consumption_batt(self, board_type):
        """ Try consumption for Battery """

        ret_val = 0
        ret_val += self.g_m.open_power_start(power='battery')

        # set a firmware on M3 to ensure corret consumption measures
        # on A8, linux is consuming enough I think
        if 'M3' == board_type:
            time.sleep(1)
            ret = self.g_m.node_flash(
                'm3', gateway_code.config.FIRMWARES['m3_autotest'])
            ret_val += self._check(ret, 'flash_m3_on_battery', ret)

        # configure consumption
        # one measure every ~0.1 seconds
        conso = Consumption(power_source='battery', board_type=board_type,
                            period='1100', average='64',
                            power=True, voltage=True, current=True)
        del self.cn_measures[:]
        ret_val += self.g_m.protocol.config_consumption(conso)

        ret_val += self.g_m.open_power_stop(power='battery')
        time.sleep(1)
        ret_val += self.g_m.open_power_start(power='battery')
        time.sleep(1)

        # stop
        ret_val += self.g_m.protocol.config_consumption(None)
        time.sleep(1)  # Flush last values

        values = []
        # measures_debug: consumption_measure
        #     1378387028.906210 0.257343 3.216250 0.080003
        for measure in self.cn_measures:
            if measure[1] == 'consumption_measure':
                values.append(tuple([float(meas) for meas in measure[3:6]]))

        test_ok = 1 < len(set(values))
        ret_val += self._check(TST_OK(test_ok), 'consumption_batt', values)

        # TODO Validate value ranges (maybe with idle firmware)
        ret_val += self.g_m.protocol.config_consumption(None)
        return ret_val

    def test_leds_with_consumption(self):
        """ Test Leds with consumption """

        _ = self.on_serial.send_command(['leds_off', '7'])

        # one measure every ~0.1 seconds
        ret_val = 0
        conso = Consumption(power_source='dc',
                            board_type=gateway_code.config.board_type(),
                            period='1100', average='64',
                            power=True, voltage=True, current=True)
        ret_val += self.g_m.open_power_start(power='dc')

        del self.cn_measures[:]
        leds_timestamps = []
        # get consumption for all leds mode:
        #     no leds, each led, all leds
        ret_val += self.g_m.protocol.config_consumption(conso)
        for leds in ['0', '1', '2', '4', '7']:
            _ = self.on_serial.send_command(['leds_on', leds])
            time.sleep(0.5)
            leds_timestamps.append(time.time())
            time.sleep(0.5)
            _ = self.on_serial.send_command(['leds_off', '7'])
        ret_val += self.g_m.protocol.config_consumption(None)
        time.sleep(0.5)  # flush last values

        # measures_debug: consumption_measure
        #     1378387028.906210  0.257343 3.216250 0.080003
        measures = [measure[2:] for measure in self.cn_measures if
                    measure[1] == 'consumption_measure']
        timestamps = [float(meas[0]) for meas in measures]

        values = []
        for led_time in leds_timestamps:
            # get power consumption at led_time
            index = bisect.bisect(timestamps, led_time)
            try:
                values.append(measures[index][1])
            except IndexError:
                values.append(float('NaN'))

        # check that consumption is higher with each led than with no leds on
        test_ok = all([val > values[0] for val in values[1:]])

        ret_val += self._check(TST_OK(test_ok), 'leds_using_conso',
                               (values[0], values[1:]))

        return ret_val
