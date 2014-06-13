#include <gtest/gtest.h>
#include <cmocka.h>

#include <math.h>
#include "mock.h"
#include "mock_fprintf.h"  // include before other includes

#include "measures_handler.c"
#include "time_ref.c"

#define OML_CONFIG_PATH "utils/oml_measures_config.xml"

static int start_called = 0;
int oml_measures_start(char *oml_config_file_path)
{
        start_called += 1;
        return 0;
}
int oml_measures_stop()
{
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

        // Invalid packet type
        data[0] = 0x00;
        ret = handle_measure_pkt(data, 0);
        ASSERT_NE(ret, 0);
}


void test_measure_handler(uint8_t *buf, struct timeval *time)
{
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

        measures_handler_start(0, OML_CONFIG_PATH);

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
        measures_handler_start(0, OML_CONFIG_PATH);
        config_consumption(PW_SRC_3_3V, 1, 1, 1);
        meas_size = mh_state.consumption.meas_len;

        expect_value(oml_measures_consumption, timestamp_s, 16);
        expect_value(oml_measures_consumption, timestamp_us, 42);
        expect_value(oml_measures_consumption, power,   1.0);
        expect_value(oml_measures_consumption, voltage, 2.0);
        expect_value(oml_measures_consumption, current, 3.0);

        expect_calls(oml_measures_consumption, 1);

        handle_measure_pkt(data, index);
        measures_handler_stop();

        /*
         * cases with non complete values
         */
        // print_measures == true for coverage
        measures_handler_start(1, OML_CONFIG_PATH);
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

        measures_handler_stop();


        // No OML
        measures_handler_start(0, NULL);
        config_consumption(PW_SRC_3_3V, 1, 0, 1);
        meas_size = mh_state.consumption.meas_len;

        expect_calls(oml_measures_consumption, 0); // no calls
        handle_measure_pkt(data, 2 + 4 + data[1] * (4 + meas_size ));

        measures_handler_stop();
}


TEST_F(test_handle_oml_measure, handle_invalid_consumption_packet)
{
        unsigned char data[64];

        // measure packet when not configured
        measures_handler_start(0, NULL);
        config_consumption(PW_SRC_3_3V, 1, 1, 1);

        data[0] = ((char)CONSUMPTION_FRAME);
        data[1] = 1; // num_measures
        int len = 42; // should be 2 + 4 + 1*(4 + meas_size)
        handle_measure_pkt(data, len);
        ASSERT_STREQ("cn_serial_error: "
                        "Invalid consumption pkt len: 42 != expected 22\n",
                        print_buff);

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
        measures_handler_start(0, OML_CONFIG_PATH);

        expect_value(oml_measures_radio, timestamp_s, 15);
        expect_value(oml_measures_radio, timestamp_us, 42);
        expect_value(oml_measures_radio, channel, 21);
        expect_value(oml_measures_radio, rssi, -42);

        expect_calls(oml_measures_radio, 1);

        handle_measure_pkt(data, index);
        measures_handler_stop();


        // with print and no OML // print not tested
        measures_handler_start(1, NULL);
        expect_calls(oml_measures_radio, 0);
        handle_measure_pkt(data, index);

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
        measures_handler_start(0, OML_CONFIG_PATH);

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
        start_called = 0;
        measures_handler_start(0, OML_CONFIG_PATH);
        measures_handler_stop();
        ASSERT_EQ(1, start_called);

        // cover case init not called
        start_called = 0;
        measures_handler_start(0, NULL);
        measures_handler_stop();
        ASSERT_EQ(0, start_called);
}
