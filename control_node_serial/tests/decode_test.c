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

#include <gtest/gtest.h>
#include "mock_fprintf.h"  // include before other includes

#include "decode.c"


/* Mock EXTERNAL dependency functions
 * with function definition
 * */

static int write_answer_called = 0;
static int write_answer_return = 0;
static int handle_measure_called = 0;
static int handle_measure_return = 0;


int write_answer(unsigned char *data, size_t len)
{
        write_answer_called++;
        return write_answer_return;

}

int handle_measure_pkt(unsigned char *data, size_t len)
{
        handle_measure_called++;
        return handle_measure_return;

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
        packet.len = 2;

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


TEST(test_decode_pkt, error_in_decode)
{
        handle_measure_called = 0;
        write_answer_called   = 0;

        struct pkt packet;
        packet.len = 2;
        packet.data[1] = 0x00;

        handle_measure_return = 1;
        write_answer_return = -42;

        packet.data[0] = 0x00;
        decode_pkt(&packet);
        ASSERT_STREQ("cn_serial_error: Error in decode packet: ret -42: " \
                        "len 2 - 0x00 0x00\n", print_buff);

        packet.data[0] = 0xFF;
        decode_pkt(&packet);
        ASSERT_STREQ("cn_serial_error: Error in decode packet: ret 1: " \
                        "len 2 - 0xFF 0x00\n", print_buff);

        ASSERT_EQ(1, handle_measure_called);
        ASSERT_EQ(1, write_answer_called);
}
