/*******************************************************************************
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
*******************************************************************************/

#include <assert.h>
#include <gtest/gtest.h>
#include <cmocka.h>
#include <string.h>
#include <arpa/inet.h>

#include <math.h>
#include "mock.h"
#include "mock_fprintf.h"  // include before other includes

#include "measures_handler.c"
#include "time_ref.c"

#define OML_CONFIG_PATH "utils/oml_measures_config.xml"

int oml_measures_start(char *oml_config_file_path, int print_measures)
{
        count_call();
        check_expected(oml_config_file_path);
        check_expected(print_measures);
        return 0;
}
int oml_measures_stop()
{
        count_call();
        return 0;
}

#define APPEND_TO_ARRAY(data, index, src, val_size) \
        do {\
                memcpy(&(data)[(index)], (src), (val_size)); \
                index += (val_size); \
        } while(0)


void oml_measures_consumption(uint32_t timestamp_s, uint32_t timestamp_us,
                double power, double voltage, double current)
{
        count_call();
        check_expected(timestamp_s);
        check_expected(timestamp_us);
        check_expected(power);
        check_expected(voltage);
        check_expected(current);
}
void oml_measures_radio(uint32_t timestamp_s, uint32_t timestamp_us,
                uint32_t channel, int32_t rssi)
{
        count_call();
        check_expected(timestamp_s);
        check_expected(timestamp_us);
        check_expected(channel);
        check_expected(rssi);
}

void oml_measures_sniffer(uint32_t timestamp_s, uint32_t timestamp_us,
                          uint32_t channel, int32_t rssi, uint32_t lqi,
                          uint8_t crc_ok, uint32_t length)
{
        count_call();
        check_expected(timestamp_s);
        check_expected(timestamp_us);
        check_expected(channel);
        check_expected(rssi);
        check_expected(lqi);
        check_expected(crc_ok);
        check_expected(length);
}


size_t sniffer_server_send_packet(const uint8_t *data, size_t len)
{
        int cmp = memcmp(data, "EX\02", 3);
        check_expected(cmp);
        return len;
}

TEST(handle_measure_pkt, test_different_packets)
{
        unsigned char data[64] = {0};
        int ret;
        data[0] = ACK_FRAME;
        ret = handle_measure_pkt(data, 0);
        ASSERT_EQ(ret, 0);

        data[0] = CONSUMPTION_FRAME;
        ret = handle_measure_pkt(data, 0);
        ASSERT_EQ(ret, 0);

        data[0] = RADIO_MEAS_FRAME;
        ret = handle_measure_pkt(data, 0);
        ASSERT_EQ(ret, 0);

        data[0] = RADIO_SNIFFER_FRAME;
        ret = handle_measure_pkt(data, 0);
        ASSERT_EQ(ret, 0);

        // Invalid packet type
        data[0] = 0x00;
        ret = handle_measure_pkt(data, 0);
        ASSERT_NE(ret, 0);
}


void test_measure_handler(uint8_t *buf, struct timeval *time)
{
        // Fake measure handler to call 'handle_oml_measure'
        count_call();
        check_expected(buf);
        check_expected(time);
}

class test_handle_oml_measure : public ::mock_tests {};
TEST_F(test_handle_oml_measure, handle_multiple_values)
{
        uint8_t data[256];
        int index = 0;

        uint32_t time_s;
        uint32_t time_us;
        struct timeval expected_time;

        uint8_t val;

        expect_calls(oml_measures_start, 1);
        expect_value(oml_measures_start, oml_config_file_path, NULL);
        expect_value(oml_measures_start, print_measures, 0);
        measures_handler_start(0, NULL);

        index = 0;
        data[index++] = 42; // measure type
        data[index++] = 0;
        time_s = 15;
        APPEND_TO_ARRAY(data, index, &time_s, sizeof(time_s));

        /* measure 1 */
        data[1]++;
        time_us = 0;
        val = 42;
        APPEND_TO_ARRAY(data, index, &time_us, sizeof(time_s));
        APPEND_TO_ARRAY(data, index, &val, sizeof(val));

        val = 42;
        expect_memory(test_measure_handler, buf, &val, sizeof(val));
        expected_time.tv_sec = 15;
        expected_time.tv_usec = 0;
        expect_memory(test_measure_handler, time, &expected_time,
                        sizeof(expected_time));

        /* measure 2 */
        data[1]++;
        time_us = 1000042;
        val = 0x42;
        APPEND_TO_ARRAY(data, index, &time_us, sizeof(time_s));
        APPEND_TO_ARRAY(data, index, &val, sizeof(val));

        val = 0x42;
        expect_memory(test_measure_handler, buf, &val, sizeof(val));
        expected_time.tv_sec  = 16;
        expected_time.tv_usec = 42;
        expect_memory(test_measure_handler, time, &expected_time,
                        sizeof(expected_time));

        // called two times
        expect_calls(test_measure_handler, 2);

        uint8_t value;
        handle_oml_measure(data, index, &value, sizeof(uint8_t),
                        test_measure_handler, "test");

        expect_calls(oml_measures_stop, 1);
        measures_handler_stop();
}

TEST_F(test_handle_oml_measure, handle_consumption_packet)
{

        uint8_t data[256];
        int index = 0;
        struct consumption_measure power;
        size_t meas_size;

        uint32_t time_s;
        uint32_t time_us;

        /* header and time reference (s) */
        index = 0;
        data[index++] = ((char)CONSUMPTION_FRAME);
        data[index++] = 0;
        time_s = 15;
        APPEND_TO_ARRAY(data, index, &time_s, sizeof(time_s));
        /* measure 1 */
        data[1]++;
        time_us = 1000042;
        APPEND_TO_ARRAY(data, index, &time_us, sizeof(time_us));
        power.val[0] = 1.0;
        power.val[1] = 2.0;
        power.val[2] = 3.0;
        APPEND_TO_ARRAY(data, index, &power, 3 * sizeof(float));

        /*
         * Run test with one packet
         */
        expect_calls(oml_measures_start, 1);
        expect_value(oml_measures_start, oml_config_file_path, NULL);
        expect_value(oml_measures_start, print_measures, 0);
        measures_handler_start(0, NULL);
        config_consumption(PW_SRC_3_3V, 1, 1, 1);
        meas_size = mh_state.consumption.meas_len;

        expect_value(oml_measures_consumption, timestamp_s, 16);
        expect_value(oml_measures_consumption, timestamp_us, 42);
        expect_value(oml_measures_consumption, power,   1.0);
        expect_value(oml_measures_consumption, voltage, 2.0);
        expect_value(oml_measures_consumption, current, 3.0);

        expect_calls(oml_measures_consumption, 1);
        handle_measure_pkt(data, index);


        /*
         * cases with non complete values
         */
        // P + C
        config_consumption(PW_SRC_3_3V, 1, 0, 1);
        meas_size = mh_state.consumption.meas_len;

        expect_value(oml_measures_consumption, timestamp_s, 16);
        expect_value(oml_measures_consumption, timestamp_us, 42);
        expect_value(oml_measures_consumption, power,   1.0);
        expect_any(oml_measures_consumption, voltage);  // NAN can't be checked
        expect_value(oml_measures_consumption, current, 2.0);

        expect_calls(oml_measures_consumption, 1);
        handle_measure_pkt(data, 2 + 4 + data[1] * (4 + meas_size ));

        // V
        config_consumption(PW_SRC_3_3V, 0, 1, 0);
        meas_size = mh_state.consumption.meas_len;

        expect_value(oml_measures_consumption, timestamp_s, 16);
        expect_value(oml_measures_consumption, timestamp_us, 42);
        expect_any(oml_measures_consumption, power);  // NAN can't be checked
        expect_value(oml_measures_consumption, voltage, 1.0);
        expect_any(oml_measures_consumption, current);

        expect_calls(oml_measures_consumption, 1);
        handle_measure_pkt(data, 2 + 4 + data[1] * (4 + meas_size ));

        expect_calls(oml_measures_stop, 1);
        measures_handler_stop();
}


TEST_F(test_handle_oml_measure, handle_invalid_consumption_packet)
{
        unsigned char data[64];

        // measure packet when not configured
        expect_calls(oml_measures_start, 1);
        expect_value(oml_measures_start, oml_config_file_path, NULL);
        expect_value(oml_measures_start, print_measures, 0);
        measures_handler_start(0, NULL);
        config_consumption(PW_SRC_3_3V, 1, 1, 1);

        data[0] = ((char)CONSUMPTION_FRAME);
        data[1] = 1; // num_measures
        int len = 42; // should be 2 + 4 + 1*(4 + meas_size)
        expect_calls(oml_measures_consumption, 0);
        handle_measure_pkt(data, len);
        ASSERT_STREQ("cn_serial_error: "
                        "Invalid consumption pkt len: 42 != expected 22\n",
                        print_buff);

        expect_calls(oml_measures_stop, 1);
        measures_handler_stop();
}

// handle_radio_measure_pkt
TEST_F(test_handle_oml_measure, handle_radio_packet)
{

        uint8_t data[256];
        int index = 0;
        struct radio_measure radio;
        size_t meas_size = sizeof(radio);  // channel rssi

        uint32_t time_s;
        uint32_t time_us;


        /* header and time reference (s) */
        index = 0;
        data[index++] = ((char)RADIO_MEAS_FRAME);
        data[index++] = 0;
        time_s = 15;
        APPEND_TO_ARRAY(data, index, &time_s, sizeof(time_s));
        /* measure 1 */
        data[1]++;
        time_us = 42;
        APPEND_TO_ARRAY(data, index, &time_us, sizeof(time_us));

        radio.channel = 21;
        radio.rssi = -42;
        APPEND_TO_ARRAY(data, index, &radio, meas_size);


        // With oml
        expect_calls(oml_measures_start, 1);
        expect_value(oml_measures_start, oml_config_file_path, NULL);
        expect_value(oml_measures_start, print_measures, 0);
        measures_handler_start(0, NULL);

        expect_value(oml_measures_radio, timestamp_s, 15);
        expect_value(oml_measures_radio, timestamp_us, 42);
        expect_value(oml_measures_radio, channel, 21);
        expect_value(oml_measures_radio, rssi, -42);

        expect_calls(oml_measures_radio, 1);

        handle_measure_pkt(data, index);
        expect_calls(oml_measures_stop, 1);
        measures_handler_stop();
}

#define JAN_1970        2208988800UL
#define FRAC       (((uint64_t)1) << 32)

TEST_F(test_handle_oml_measure, handle_radio_sniffer)
{

        uint8_t data[256];
        int index = 0;

        uint16_t device_id = 3042;
        uint32_t seqno = 1;

        struct timeval timestamp = {42, 500000};
        uint32_t t_ntp_msb = htonl((uint32_t)((uint64_t)42 + JAN_1970));
        uint32_t t_ntp_lsb = htonl((uint32_t)(((uint64_t)500000 * FRAC)/1000000));

        uint16_t rx_time_len = 4000;
        uint8_t channel = 11;
        int8_t rssi = -91;
        uint8_t lqi = 254;

        data[index++] = ((char)RADIO_SNIFFER_FRAME);
        data[index++] = 'E';
        data[index++] = 'X';
        data[index++] = '\02';
        data[index++] = '1';  // Type Data
        data[index++] = channel;
        APPEND_TO_ARRAY(data, index, &device_id, sizeof(device_id));
        data[index++] = 0;    // LQI Mode
        data[index++] = lqi;


        APPEND_TO_ARRAY(data, index, &t_ntp_msb, sizeof(t_ntp_msb));
        APPEND_TO_ARRAY(data, index, &t_ntp_lsb, sizeof(t_ntp_lsb));
        APPEND_TO_ARRAY(data, index, &seqno,     sizeof(seqno));

        // Add reserved bytes with our data
        uint8_t reserved[10] = {0};
        int idx = 0;
        APPEND_TO_ARRAY(reserved, idx, &rx_time_len, sizeof(rx_time_len));
        reserved[idx++] = (uint8_t)rssi;
        APPEND_TO_ARRAY(data, index, &reserved, sizeof(reserved));

        // Add payload now
        int header_len = index;
        uint8_t pkt_len = 0;


        // No payload; let only 2 bytes as they are added for 'fake_crc'
        index = header_len;
        pkt_len = 2;
        data[index++] = pkt_len;
        index += pkt_len;


        // invalid len
        expect_calls(oml_measures_sniffer, 0);
        handle_radio_sniffer(data, index -1);

        // valid len
        expect_value(oml_measures_sniffer, timestamp_s,  timestamp.tv_sec);
        expect_value(oml_measures_sniffer, timestamp_us, timestamp.tv_usec);
        expect_value(oml_measures_sniffer, channel,      channel);
        expect_value(oml_measures_sniffer, crc_ok,       1);
        expect_value(oml_measures_sniffer, rssi,         rssi);
        expect_value(oml_measures_sniffer, lqi,          lqi);
        expect_value(oml_measures_sniffer, length,       pkt_len -2);

        expect_value(sniffer_server_send_packet, cmp, 0);
        expect_calls(oml_measures_sniffer, 1);
        handle_radio_sniffer(data, index);


        // full packet
        index = header_len;
        pkt_len = 125;
        data[index++] = pkt_len;
        index += pkt_len;


        // invalid len
        expect_calls(oml_measures_sniffer, 0);
        handle_radio_sniffer(data, index -1);

        // valid len
        expect_value(oml_measures_sniffer, timestamp_s,  timestamp.tv_sec);
        expect_value(oml_measures_sniffer, timestamp_us, timestamp.tv_usec);
        expect_value(oml_measures_sniffer, channel,      channel);
        expect_value(oml_measures_sniffer, crc_ok,       1);
        expect_value(oml_measures_sniffer, rssi,         rssi);
        expect_value(oml_measures_sniffer, lqi,          lqi);
        expect_value(oml_measures_sniffer, length,       pkt_len -2);

        expect_value(sniffer_server_send_packet, cmp, 0);
        expect_calls(oml_measures_sniffer, 1);
        handle_radio_sniffer(data, index);

        expect_calls(oml_measures_stop, 1);
        measures_handler_stop();
}


// handle_ack_pkt
TEST(handle_ack_pkt, set_time)
{
        unsigned char data[3] = {0};
        data[1] = SET_TIME;
        data[2] = 0; // unused
        gettimeofday(&set_time_ref, NULL);
        handle_ack_pkt(data, 3);  // nothing done maybe remove me?

        ASSERT_EQ(0, set_time_ref.tv_sec);
        ASSERT_EQ(0, set_time_ref.tv_usec);

}

TEST(handle_ack_pkt, power_poll_ack)
{
        unsigned char data[8];
        data[1] = CONFIG_CONSUMPTION;
        expect_calls(oml_measures_start, 1);
        expect_value(oml_measures_start, oml_config_file_path, NULL);
        expect_value(oml_measures_start, print_measures, 0);
        measures_handler_start(0, NULL);

        // PC
        data[2]  = 0;
        data[2] |= PW_SRC_BATT;
        data[2] |= MEASURE_POWER;
        data[2] |= MEASURE_CURRENT;
        handle_ack_pkt(data, 3);

        ASSERT_EQ(1, mh_state.consumption.p);
        ASSERT_EQ(0, mh_state.consumption.v);
        ASSERT_EQ(1, mh_state.consumption.c);

        // V
        data[2]  = 0;
        data[2] |= PW_SRC_3_3V;
        data[2] |= MEASURE_VOLTAGE;
        handle_ack_pkt(data, 3);

        ASSERT_EQ(0, mh_state.consumption.p);
        ASSERT_EQ(1, mh_state.consumption.v);
        ASSERT_EQ(0, mh_state.consumption.c);

        expect_calls(oml_measures_stop, 1);
        measures_handler_stop();
}

TEST(handle_ack_pkt, radio_acks)
{
        unsigned char data[8];

        data[1] = CONFIG_RADIO_STOP;
        handle_ack_pkt(data, 1);
        ASSERT_STREQ("config_ack config_radio_stop\n", print_buff);

        data[1] = CONFIG_RADIO_MEAS;
        handle_ack_pkt(data, 1);
        ASSERT_STREQ("config_ack config_radio_measure\n", print_buff);

}

TEST(handle_ack_pkt, invalid_msgs)
{
        unsigned char data[8];
        data[1] = 0x00; // not a real ack type
        handle_ack_pkt(data, 3);
        ASSERT_STREQ("cn_serial_error: Unkown ACK frame 0x00\n", print_buff);
}

TEST(calculate_time, overflow_on_usec_sum)
{
        struct timeval time_final;
        unsigned int cn_time;

        calculate_time_extended(&time_final, 1, 1500000);
        ASSERT_EQ(2, time_final.tv_sec);
        ASSERT_EQ(500000, time_final.tv_usec);
}


// init_measures_handler
TEST(init_measures_handler, test)
{
        expect_calls(oml_measures_start, 1);
        expect_value(oml_measures_start, oml_config_file_path, OML_CONFIG_PATH);
        expect_value(oml_measures_start, print_measures, 1);
        measures_handler_start(1, OML_CONFIG_PATH);
        expect_calls(oml_measures_stop, 1);
        measures_handler_stop();

        expect_calls(oml_measures_start, 1);
        expect_value(oml_measures_start, oml_config_file_path, NULL);
        expect_value(oml_measures_start, print_measures, 0);
        measures_handler_start(0, NULL);
        expect_calls(oml_measures_stop, 1);
        measures_handler_stop();
}
