#include <gtest/gtest.h>

#include <math.h>
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

static int consumption_mock_called = 0;
static struct {
        uint32_t timestamp_s;
        uint32_t timestamp_us;
        double current;
        double voltage;
        double power;
} consumption_call_args;

void oml_measures_consumption(uint32_t timestamp_s, uint32_t timestamp_us,
                double power, double voltage, double current)
{
        consumption_call_args.timestamp_s = timestamp_s;
        consumption_call_args.timestamp_us = timestamp_us;
        consumption_call_args.current = current;
        consumption_call_args.voltage = voltage;
        consumption_call_args.power = power;
        consumption_mock_called +=1;
}
static int radio_mock_called = 0;
static struct {
        uint32_t timestamp_s;
        uint32_t timestamp_us;
        uint32_t channel;
        int32_t rssi;
} radio_call_args;
void oml_measures_radio(uint32_t timestamp_s, uint32_t timestamp_us,
                uint32_t channel, int32_t rssi)
{
        radio_call_args.timestamp_s = timestamp_s;
        radio_call_args.timestamp_us = timestamp_us;
        radio_call_args.channel = channel;
        radio_call_args.rssi = rssi;
        radio_mock_called +=1;
}


/*
 * Mock exit, mocking directly cause
 *     warning: 'noreturn' function does return [enabled by default]
 */

// handle_measure_pkt
TEST(handle_measure_pkt, test_different_packets)
{
        unsigned char data[64];
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


// handle_pw_pkt
TEST(handle_pw_pkt, coverage_for_pw_pkt_different_configuration)
{
        unsigned char data[256];

        struct power_vals power;
        size_t data_size;

        consumption_mock_called = 0;

        measures_handler_start(0, OML_CONFIG_PATH);
        mh_state.power.power_source = (char) PW_SRC_3_3V;
        mh_state.power.is_valid = 1;
        mh_state.power.p = 1;
        mh_state.power.v = 1;
        mh_state.power.c = 1;
        data_size = sizeof(unsigned int) + 3*sizeof(float);
        mh_state.power.raw_values_len = data_size;

        int index = 0;
        data[index++] = ((char)CONSUMPTION_FRAME);
        data[index++] = 0;

        uint32_t t_ref_s = 15;
        memcpy(&data[index], &t_ref_s, sizeof(uint32_t));
        index += sizeof(uint32_t);

        power.time_us = (unsigned int) 0;
        power.val[0] = 1.0;
        power.val[1] = 2.0;
        power.val[2] = 3.0;
        memcpy(&data[index], &power, data_size);
        index += data_size;


        // num == 1
        data[1] = 1;
        handle_pw_pkt(data, index);
        ASSERT_EQ(1, consumption_mock_called);
        ASSERT_EQ(15, consumption_call_args.timestamp_s);
        ASSERT_EQ(0, consumption_call_args.timestamp_us);
        ASSERT_EQ(1.0, consumption_call_args.power);
        ASSERT_EQ(2.0, consumption_call_args.voltage);
        ASSERT_EQ(3.0, consumption_call_args.current);

        // num == 2
        data[1] = 2;
        power.time_us = (unsigned int) 1000042;
        power.val[0] = 4.0;
        power.val[1] = 5.0;
        power.val[2] = 6.0;
        memcpy(&data[index], &power, data_size);
        index += data_size;
        consumption_mock_called = 0;

        handle_pw_pkt(data, index);
        ASSERT_EQ(2, consumption_mock_called);
        ASSERT_EQ(16, consumption_call_args.timestamp_s);
        ASSERT_EQ(42, consumption_call_args.timestamp_us);
        ASSERT_EQ(4.0, consumption_call_args.power);
        ASSERT_EQ(5.0, consumption_call_args.voltage);
        ASSERT_EQ(6.0, consumption_call_args.current);

        measures_handler_stop();



        consumption_mock_called = 0;
        measures_handler_start(1, OML_CONFIG_PATH); // print_measures == true for coverage
        // P + C
        mh_state.power.power_source = (char) PW_SRC_3_3V;
        mh_state.power.is_valid = 1;
        mh_state.power.p = 1;
        mh_state.power.v = 0;
        mh_state.power.c = 1;
        data_size = sizeof(unsigned int) + 2*sizeof(float);
        mh_state.power.raw_values_len = data_size;

        data[1] = 1;
        handle_pw_pkt(data, 2 + 4 + data[1] * data_size);
        ASSERT_EQ(1, consumption_mock_called);
        ASSERT_EQ(15, consumption_call_args.timestamp_s);
        ASSERT_EQ(0, consumption_call_args.timestamp_us);
        ASSERT_EQ(1.0, consumption_call_args.power);
        ASSERT_TRUE(isnan(consumption_call_args.voltage));
        ASSERT_EQ(2.0, consumption_call_args.current);



        // only V
        mh_state.power.p = 0;
        mh_state.power.v = 1;
        mh_state.power.c = 0;
        data_size = sizeof(unsigned int) + 2*sizeof(float);
        mh_state.power.raw_values_len = data_size;
        data[1] = 1;
        handle_pw_pkt(data, 2 + 4 + data[1] * data_size);
        ASSERT_EQ(2, consumption_mock_called);

        ASSERT_EQ(15, consumption_call_args.timestamp_s);
        ASSERT_EQ(0, consumption_call_args.timestamp_us);
        ASSERT_TRUE(isnan(consumption_call_args.power));
        ASSERT_EQ(1.0, consumption_call_args.voltage);
        ASSERT_TRUE(isnan(consumption_call_args.current));

        measures_handler_stop();

        // No OML
        consumption_mock_called = 0;
        measures_handler_start(0, NULL);
        // P + C
        mh_state.power.power_source = (char) PW_SRC_3_3V;
        mh_state.power.is_valid = 1;
        mh_state.power.p = 1;
        mh_state.power.v = 0;
        mh_state.power.c = 1;
        data_size = sizeof(unsigned int) + 2*sizeof(float);
        mh_state.power.raw_values_len = data_size;
        data[1] = 1;
        handle_pw_pkt(data, 2 + data[1] * data_size);
        measures_handler_stop();

        ASSERT_EQ(0, consumption_mock_called);
}

TEST(handle_pw_pkt, invalid_calls)
{
        unsigned char data[64];

        // measure packet when not configured
        measures_handler_start(0, OML_CONFIG_PATH);
        handle_pw_pkt(data, 0);
        ASSERT_STREQ("cn_serial_error: "
                        "Got PW measure without being configured\n",
                        print_buff);

        // invalid packet length received
        mh_state.power.raw_values_len = 4 + 3*4;
        mh_state.power.is_valid = 1;
        data[1] = 1; // num_measures
        int len = 10; // 4 + 1*4 + 2
        handle_pw_pkt(data, len);
        ASSERT_STREQ("cn_serial_error: "
                        "Invalid consumption pkt len: 10 != expected 22\n",
                        print_buff);
        measures_handler_stop();
}


// handle_radio_measure_pkt
TEST(handle_radio_measure_pkt, coverage_for_pw_pkt_different_configuration)
{
        unsigned char data[256];
        struct radio_measure_vals radio;
        size_t data_size = 6;

        measures_handler_start(0, OML_CONFIG_PATH);
        memset(print_buff, '\0', sizeof(print_buff));

        int index = 0;
        data[index++] = ((char)RADIO_MEAS_FRAME);
        data[index++] = 1;  // measure_count

        uint32_t t_ref_s = 15;
        memcpy(&data[index], &t_ref_s, sizeof(uint32_t));
        index += sizeof(uint32_t);

        // first value
        radio.time_us = (unsigned int) 0;
        radio.channel = 21;
        radio.rssi = -42;
        memcpy(&data[index], &radio, data_size);
        index += data_size;


        // num == 1
        radio_mock_called = 0;
        data[1] = 1;
        handle_radio_measure_pkt(data, 2 + 4 + data[1] * data_size);
        ASSERT_EQ(1, radio_mock_called);

        ASSERT_EQ(15, radio_call_args.timestamp_s);
        ASSERT_EQ(0, radio_call_args.timestamp_us);
        ASSERT_EQ(21, radio_call_args.channel);
        ASSERT_EQ(-42, radio_call_args.rssi);
        measures_handler_stop();

        // num == 2
        radio.time_us = (unsigned int) 1000000;
        radio.channel = 25;
        radio.rssi = 42;
        memcpy(&data[index], &radio, data_size);
        index += data_size;
        radio_mock_called = 0;
        measures_handler_start(1, OML_CONFIG_PATH); // print_measures == true for coverage
        data[1] = 2;

        handle_radio_measure_pkt(data, 2 + 4 + data[1] * data_size);
        ASSERT_EQ(2, radio_mock_called);

        ASSERT_EQ(16, radio_call_args.timestamp_s);
        ASSERT_EQ(0, radio_call_args.timestamp_us);
        ASSERT_EQ(25, radio_call_args.channel);
        ASSERT_EQ(42, radio_call_args.rssi);
        measures_handler_stop();

        // NO OML
        radio_mock_called = 0;
        measures_handler_start(0, NULL);
        handle_radio_measure_pkt(data, 2 + 4 + data[1] * data_size);
        measures_handler_stop();
        ASSERT_EQ(0, radio_mock_called);

}


// handle_ack_pkt
TEST(handle_ack_pkt, set_time)
{
        unsigned char data[8];
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

        ASSERT_TRUE(mh_state.power.is_valid);
        ASSERT_EQ(1, mh_state.power.p);
        ASSERT_EQ(0, mh_state.power.v);
        ASSERT_EQ(1, mh_state.power.c);

        // V
        data[2]  = 0;
        data[2] |= PW_SRC_3_3V;
        data[2] |= MEASURE_VOLTAGE;
        handle_ack_pkt(data, 3);

        ASSERT_TRUE(mh_state.power.is_valid);
        ASSERT_EQ(0, mh_state.power.p);
        ASSERT_EQ(1, mh_state.power.v);
        ASSERT_EQ(0, mh_state.power.c);

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
        mh_state.power.is_valid = 42;
        start_called = 0;
        measures_handler_start(0, OML_CONFIG_PATH);
        ASSERT_EQ(0, mh_state.power.is_valid);
        measures_handler_stop();
        ASSERT_EQ(1, start_called);

        // cover case init not called
        start_called = 0;
        measures_handler_start(0, NULL);
        measures_handler_stop();
        ASSERT_EQ(0, start_called);
}
