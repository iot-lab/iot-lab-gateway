#include <gtest/gtest.h>
/* Mock log_print */
char print_buff[2048];
#define fprintf(stream, ...)  snprintf(print_buff, sizeof(print_buff), __VA_ARGS__)


#include "time_update.c"
#include "measures_handler.c"


/*
 * Mock exit, mocking directly cause
 *     warning: 'noreturn' function does return [enabled by default]
 */

TEST(handle_measure_pkt, test_different_packets)
{
        unsigned char data[64];
        int ret;
        data[0] = ACK_FRAME;
        ret = handle_measure_pkt(data, 0);
        ASSERT_EQ(ret, 0);

        data[0] = PW_POLL_FRAME;
        ret = handle_measure_pkt(data, 0);
        ASSERT_EQ(ret, 0);

        data[0] = RADIO_POLL_FRAME;
        ret = handle_measure_pkt(data, 0);
        ASSERT_NE(ret, 0); // NOT IMPLEMENTED

        // Invalid packet type
        data[0] = 0x00;
        ret = handle_measure_pkt(data, 0);
        ASSERT_NE(ret, 0);
}




TEST(handle_pw_pkt, coverage_for_pw_pkt_different_configuration)
{
        unsigned char data[256];
        data[0] = ((char)PW_POLL_FRAME);
        data[1] = 2;
        struct power_vals power;
        size_t data_size;


        init_measures_handler();
        mh_state.power.power_source = (char) SOURCE_3_3V;
        mh_state.power.is_valid = 1;
        mh_state.power.p = 1;
        mh_state.power.v = 1;
        mh_state.power.c = 1;
        data_size = sizeof(unsigned int) + 3*sizeof(float);
        mh_state.power.raw_values_len = data_size;

        power.time = (unsigned int) 0;
        power.val[0] = 1.0;
        power.val[1] = 2.0;
        power.val[2] = 3.0;
        memcpy(&data[2], &power, data_size);

        power.time = (unsigned int) TIME_FACTOR;  // 1sec in tics
        power.val[0] = 4.0;
        power.val[1] = 5.0;
        power.val[2] = 6.0;
        memcpy(&data[2 + data_size], &power, data_size);

        // num == 1
        data[1] = 1;
        handle_pw_pkt(data, 2 + data[1] * data_size);
        ASSERT_STREQ("0.0:0.0: 1.000000 2.000000 3.000000\n", print_buff);
        // num == 2
        data[1] = 2;
        handle_pw_pkt(data, 2 + data[1] * data_size);
        ASSERT_STREQ("0.0:1.0: 4.000000 5.000000 6.000000\n", print_buff);



        // P + C
        mh_state.power.p = 1;
        mh_state.power.v = 0;
        mh_state.power.c = 1;
        data_size = sizeof(unsigned int) + 2*sizeof(float);
        mh_state.power.raw_values_len = data_size;
        data[1] = 1;
        handle_pw_pkt(data, 2 + data[1] * data_size);
        ASSERT_STREQ("0.0:0.0: 1.000000 0.000000 2.000000\n", print_buff);


        // only V
        mh_state.power.p = 0;
        mh_state.power.v = 1;
        mh_state.power.c = 0;
        data_size = sizeof(unsigned int) + 2*sizeof(float);
        mh_state.power.raw_values_len = data_size;
        data[1] = 1;
        handle_pw_pkt(data, 2 + data[1] * data_size);
        ASSERT_STREQ("0.0:0.0: 0.000000 1.000000 0.000000\n", print_buff);






}

TEST(handle_pw_pkt, invalid_calls)
{
        unsigned char data[64];

        // measure packet when not configured
        init_measures_handler();
        handle_pw_pkt(data, 0);
        ASSERT_STREQ("cn_serial_error : "
                        "Got PW measure without being configured\n",
                        print_buff);

        // invalid packet length received
        mh_state.power.raw_values_len = 4 + 3*4;
        mh_state.power.is_valid = 1;
        data[1] = 1; // num_measures
        int len = 10; // 4 + 1*4 + 2
        handle_pw_pkt(data, len);
        ASSERT_STREQ("cn_serial_error : "
                        "Invalid measure pkt len: 10 != expected 18\n",
                        print_buff);
}

TEST(handle_ack_pkt, reset_time)
{
        unsigned char data[8];
        data[1] = RESET_TIME;
        data[2] = 0; // unused
        new_time_ref.tv_sec  = 0xDEAD;
        new_time_ref.tv_usec = 0xBEEF;
        handle_ack_pkt(data, 3);

        ASSERT_EQ(mh_state.time_ref.tv_sec, 0xDEAD);
        ASSERT_EQ(mh_state.time_ref.tv_usec, 0xBEEF);
}


TEST(handle_ack_pkt, power_poll_ack)
{
        unsigned char data[8];
        data[1] = CONFIG_POWER_POLL;
        init_measures_handler();

        // PC
        data[2]  = 0;
        data[2] |= SOURCE_BATT;
        data[2] |= MEASURE_POWER;
        data[2] |= MEASURE_CURRENT;
        handle_ack_pkt(data, 3);

        ASSERT_TRUE(mh_state.power.is_valid);
        ASSERT_EQ(1, mh_state.power.p);
        ASSERT_EQ(0, mh_state.power.v);
        ASSERT_EQ(1, mh_state.power.c);

        // V
        data[2]  = 0;
        data[2] |= SOURCE_3_3V;
        data[2] |= MEASURE_VOLTAGE;
        handle_ack_pkt(data, 3);

        ASSERT_TRUE(mh_state.power.is_valid);
        ASSERT_EQ(0, mh_state.power.p);
        ASSERT_EQ(1, mh_state.power.v);
        ASSERT_EQ(0, mh_state.power.c);

}




TEST(handle_ack_pkt, invalid_msgs)
{
        unsigned char data[8];
        handle_ack_pkt(data, 2); // invalid len
        ASSERT_STREQ("cn_serial_error : Invalid len for ACK 2\n", print_buff);

        data[1] = 0x00; // not a real ack type
        handle_ack_pkt(data, 3);
        ASSERT_STREQ("cn_serial_error : Unkown ACK frame 0x00\n", print_buff);
}


TEST(init_measures_handler, test)
{
        mh_state.time_ref.tv_sec = 0xDEAD;
        mh_state.time_ref.tv_usec = 0xBEEF;
        mh_state.power.is_valid = 42;
        init_measures_handler();
        ASSERT_EQ(0, mh_state.time_ref.tv_sec);
        ASSERT_EQ(0, mh_state.time_ref.tv_usec);
        ASSERT_EQ(0, mh_state.power.is_valid);
}
