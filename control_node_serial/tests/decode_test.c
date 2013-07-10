#include <gtest/gtest.h>
#include "decode.c"


/* Mock EXTERNAL dependency functions
 * with function definition
 * */

static int write_answer_called = 0;
static int handle_measure_called = 0;


int write_answer(unsigned char *data, size_t len)
{
        write_answer_called++;
        return 0;

}

int handle_measure_pkt(unsigned char *data, size_t len)
{
        handle_measure_called++;
        return 0;

}


TEST(test_decode_pkt, packet_measures)
{
        handle_measure_called = 0;
        write_answer_called   = 0;
        struct pkt packet;
        packet.len = 1;

        packet.data[0] = 0xFF;
        decode_pkt(&packet);
        packet.data[0] = 0xFA;
        decode_pkt(&packet);
        packet.data[0] = 0xFE;
        decode_pkt(&packet);

        ASSERT_EQ(3, handle_measure_called);
        ASSERT_EQ(0, write_answer_called);
}

TEST(test_decode_pkt, packet_answer_command)
{
        handle_measure_called = 0;
        write_answer_called   = 0;
        struct pkt packet;
        packet.len = 1;

        // start, stop, reset
        packet.data[0] = 0x70;
        decode_pkt(&packet);
        packet.data[0] = 0x71;
        decode_pkt(&packet);
        packet.data[0] = 0x72;
        decode_pkt(&packet);

        // measure config
        packet.data[0] = 0x74;
        decode_pkt(&packet);
        packet.data[0] = 0x75;
        decode_pkt(&packet);
        packet.data[0] = 0x76;
        decode_pkt(&packet);
        packet.data[0] = 0x77;
        decode_pkt(&packet);
        packet.data[0] = 0x78;
        decode_pkt(&packet);
        packet.data[0] = 0x79;
        decode_pkt(&packet);

        // error frame
        packet.data[0] = 0xEE;
        decode_pkt(&packet);

        ASSERT_EQ(0, handle_measure_called);
        ASSERT_EQ(10, write_answer_called);
}


