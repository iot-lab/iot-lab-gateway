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
#include <unistd.h> // sleep, size_t

#include "mock_fprintf.h"  // include before other includes

/*
 * Mock exit, mocking directly cause
 *     warning: 'noreturn' function does return [enabled by default]
 */
#define exit(status)  mock_exit(status)
void mock_exit(int status);


#include "command_reader.c"
#include "command_parser.c"  // MAYBE REMOVE LATER
struct timeval set_time_ref;

uint16_t sniffer_zep_node_id;  // needed by sniffer_zep


/* Mock EXTERNAL dependency functions
 * with function definition
 */
// Don't want to mock these
#include "utils.c"


/*
 *  Test parse_cmd
 */
TEST(test_parse_cmd, simple_commands)
{
        int ret;
        uint32_t time_s;
        struct command_buffer cmd_buff;
        char cmd[256];
        struct timeval time_now;
        gettimeofday(&time_now, NULL);

        strcpy(cmd, "set_time");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(9, cmd_buff.u.s.len);
        ASSERT_EQ(SET_TIME, cmd_buff.u.s.payload[0]);
        // check time stored in the packet is correct
        memcpy(&time_s, &cmd_buff.u.s.payload[1], sizeof(uint32_t));
        ASSERT_TRUE(time_s <= time_now.tv_sec);
        ASSERT_TRUE(time_s + 2 >= time_now.tv_sec);

        uint16_t node_id;
        strcpy(cmd, "set_node_id m3 1");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(3, cmd_buff.u.s.len);
        ASSERT_EQ(SET_NODE_ID, cmd_buff.u.s.payload[0]);
        memcpy(&node_id, &cmd_buff.u.s.payload[1], sizeof(uint16_t));
        ASSERT_EQ(0x3001, node_id);

        strcpy(cmd, "set_node_id a8 266");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(3, cmd_buff.u.s.len);
        ASSERT_EQ(SET_NODE_ID, cmd_buff.u.s.payload[0]);
        memcpy(&node_id, &cmd_buff.u.s.payload[1], sizeof(uint16_t));
        ASSERT_EQ(0x810A, node_id);


        strcpy(cmd, "start dc");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(2, cmd_buff.u.s.len);
        ASSERT_EQ(OPEN_NODE_START, cmd_buff.u.s.payload[0]);

        strcpy(cmd, "stop battery");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(2, cmd_buff.u.s.len);
        ASSERT_EQ(OPEN_NODE_STOP, cmd_buff.u.s.payload[0]);

        // leds
        strcpy(cmd, "green_led_on");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(1, cmd_buff.u.s.len);
        ASSERT_EQ(GREEN_LED_ON, cmd_buff.u.s.payload[0]);
        strcpy(cmd, "green_led_blink");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(1, cmd_buff.u.s.len);
        ASSERT_EQ(GREEN_LED_BLINK, cmd_buff.u.s.payload[0]);
}

TEST(test_parse_cmd, consumption)
{
        /*
         * Sending multiple config_consumption_measure commands
         * and checking that the configuration is different each time
         */
        int ret;
        struct command_buffer cmd_buff;
        char cmd[256] = {0};


        strcpy(cmd, "config_consumption_measure stop");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(4, cmd_buff.u.s.len);
        ASSERT_EQ(CONFIG_CONSUMPTION, cmd_buff.u.s.payload[0]);
        ASSERT_EQ(STOP, cmd_buff.u.s.payload[1]);

        strcpy(cmd, "config_consumption_measure start 3.3V p 1 v 1 c 1 -p 140 -a 1");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(4, cmd_buff.u.s.len);
        ASSERT_EQ(CONFIG_CONSUMPTION, cmd_buff.u.s.payload[0]);
        ASSERT_EQ(START, cmd_buff.u.s.payload[1]);
        // save payload to check that each other config is different
        unsigned payload_1_2 = cmd_buff.u.s.payload[3] << 8 | cmd_buff.u.s.payload[2];

        strcpy(cmd, "config_consumption_measure start BATT p 1 v 1 c 1 -p 140 -a 1");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_NE(payload_1_2, cmd_buff.u.s.payload[3] << 8 | cmd_buff.u.s.payload[2]);

        strcpy(cmd, "config_consumption_measure start 3.3V p 0 v 1 c 0 -p 140 -a 1");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_NE(payload_1_2, cmd_buff.u.s.payload[3] << 8 | cmd_buff.u.s.payload[2]);

        strcpy(cmd, "config_consumption_measure start 3.3V p 1 v 0 c 1 -p 140 -a 1");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_NE(payload_1_2, cmd_buff.u.s.payload[3] << 8 | cmd_buff.u.s.payload[2]);

        strcpy(cmd, "config_consumption_measure start 3.3V p 1 v 1 c 1 -p 8244 -a 1024");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_NE(payload_1_2, cmd_buff.u.s.payload[3] << 8 | cmd_buff.u.s.payload[2]);

        strcpy(cmd, "config_consumption_measure");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_NE(0, ret);

        strcpy(cmd, "config_consumption_measure start invalid_args");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_NE(0, ret);

        strcpy(cmd, "config_consumption_measure inval_cmd");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_NE(0, ret);

        strcpy(cmd, "config_consumption_measure inval 3.3V p 1 v 1 c 1 -p 8244 -a 1024");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_NE(0, ret);
}

TEST(test_parse_cmd, radio_stop)
{
        int ret;
        char cmd[256];
        struct command_buffer cmd_buff;

        strcpy(cmd, "config_radio_stop");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(1, cmd_buff.u.s.len);
        ASSERT_EQ(CONFIG_RADIO_STOP, cmd_buff.u.s.payload[0]);
}

TEST(test_parse_cmd, radio_measure)
{
        int ret;
        struct command_buffer cmd_buff;
        char cmd[256];


        strcpy(cmd, "config_radio_measure 11 100 0");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(8, cmd_buff.u.s.len);
        ASSERT_EQ(CONFIG_RADIO_MEAS, cmd_buff.u.s.payload[0]);
        // CHAN
        ASSERT_EQ(0, cmd_buff.u.s.payload[1]);
        ASSERT_EQ(1 << 11-8, cmd_buff.u.s.payload[2]);
        ASSERT_EQ(0, cmd_buff.u.s.payload[3]);
        ASSERT_EQ(0, cmd_buff.u.s.payload[4]);
        // PERIOD
        ASSERT_EQ(100, cmd_buff.u.s.payload[5]);
        ASSERT_EQ(0, cmd_buff.u.s.payload[6]);
        // num measures
        ASSERT_EQ(0, cmd_buff.u.s.payload[7]);

        strcpy(cmd, "config_radio_measure 16,17,18 256 10");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(8, cmd_buff.u.s.len);
        ASSERT_EQ(CONFIG_RADIO_MEAS, cmd_buff.u.s.payload[0]);
        ASSERT_EQ(7, cmd_buff.u.s.payload[3]);
        ASSERT_EQ(1, cmd_buff.u.s.payload[6]);
        ASSERT_EQ(10, cmd_buff.u.s.payload[7]);



        strcpy(cmd, "config_radio_measure invalid");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_NE(0, ret);

        // min to 1
        strcpy(cmd, "config_radio_measure 15 0 1");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_NE(0, ret);

        // max to 2^16
        strcpy(cmd, "config_radio_measure 15 65536 1");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_NE(0, ret);

        // invalid channel list
        strcpy(cmd, "config_radio_measure 10,27 1 1");
        ret = parse_cmd(cmd, &cmd_buff);
        //ASSERT_NE(0, ret);
}

TEST(test_parse_cmd, radio_sniffer)
{
        int ret;
        struct command_buffer cmd_buff;
        char cmd[256];

        strcpy(cmd, "config_radio_sniffer 11 0");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(7, cmd_buff.u.s.len);
        ASSERT_EQ(CONFIG_RADIO_SNIFFER, cmd_buff.u.s.payload[0]);
        // CHAN
        ASSERT_EQ(0, cmd_buff.u.s.payload[1]);
        ASSERT_EQ(1 << 11-8, cmd_buff.u.s.payload[2]);
        ASSERT_EQ(0, cmd_buff.u.s.payload[3]);
        ASSERT_EQ(0, cmd_buff.u.s.payload[4]);
        // PERIOD
        ASSERT_EQ(0, cmd_buff.u.s.payload[5]);
        ASSERT_EQ(0, cmd_buff.u.s.payload[6]);


        strcpy(cmd, "config_radio_sniffer 16,17,18 256");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(7, cmd_buff.u.s.len);
        ASSERT_EQ(CONFIG_RADIO_SNIFFER, cmd_buff.u.s.payload[0]);
        ASSERT_EQ(7, cmd_buff.u.s.payload[3]);
        ASSERT_EQ(1, cmd_buff.u.s.payload[6]);
}


TEST(test_parse_cmd, test_commands)
{
        int ret;
        struct command_buffer cmd_buff;
        char cmd[256];

        /* ping pong */
        strcpy(cmd, "test_radio_ping_pong start 15 3dBm");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(4, cmd_buff.u.s.len);
        ASSERT_EQ(TEST_RADIO_PING_PONG, cmd_buff.u.s.payload[0]);

        strcpy(cmd, "test_radio_ping_pong stop");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(4, cmd_buff.u.s.len);
        ASSERT_EQ(TEST_RADIO_PING_PONG, cmd_buff.u.s.payload[0]);
        ASSERT_EQ(STOP, cmd_buff.u.s.payload[1]);

        strcpy(cmd, "test_radio_ping_pong start 10 3dBm");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_NE(0, ret);
        strcpy(cmd, "test_radio_ping_pong start 27 0dBm");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_NE(0, ret);
        strcpy(cmd, "test_radio_ping_pong start");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_NE(0, ret);

        strcpy(cmd, "test_radio_ping_pong invalid");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_NE(0, ret);


        /* gpio */
        strcpy(cmd, "test_gpio start");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(2, cmd_buff.u.s.len);
        ASSERT_EQ(TEST_GPIO, cmd_buff.u.s.payload[0]);

        strcpy(cmd, "test_gpio stop");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(2, cmd_buff.u.s.len);
        ASSERT_EQ(TEST_GPIO, cmd_buff.u.s.payload[0]);


        /* i2c */
        strcpy(cmd, "test_i2c start");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(2, cmd_buff.u.s.len);
        ASSERT_EQ(TEST_I2C2, cmd_buff.u.s.payload[0]);

        strcpy(cmd, "test_i2c stop");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(2, cmd_buff.u.s.len);
        ASSERT_EQ(TEST_I2C2, cmd_buff.u.s.payload[0]);

        /* pps */
        strcpy(cmd, "test_pps start");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(2, cmd_buff.u.s.len);
        ASSERT_EQ(TEST_PPS, cmd_buff.u.s.payload[0]);

        strcpy(cmd, "test_pps stop");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(2, cmd_buff.u.s.len);
        ASSERT_EQ(TEST_PPS, cmd_buff.u.s.payload[0]);

        strcpy(cmd, "test_got_pps");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(1, cmd_buff.u.s.len);
        ASSERT_EQ(TEST_GOT_PPS, cmd_buff.u.s.payload[0]);

}

/*
 * Test read_commands
 */

static int write_called = 0;
ssize_t write(int fd, const void *buf, size_t count)
{
        write_called++;
        return count;
}
static int mock_exit_called = 0;
void mock_exit(int status)
{
        (void) status;
        mock_exit_called++;
}

static int index_line = 0;
static char *lines[2] = {
        "start dc\n",
        "invalid_command lalal\n"
};
ssize_t getline(char **lineptr, size_t *n, FILE *stream)
{
        if (index_line == 2)
                return -1;
        int len = strlen(strcpy(*lineptr, lines[index_line]));
        index_line++;
        return len;

}


TEST(test_read_commands, test_with_exit)
{
        mock_exit_called = 0;
        write_called = 0;

        read_commands(&reader_state);
        ASSERT_EQ(1, mock_exit_called);
        ASSERT_EQ(1, write_called);
}





/*
 *  Test write_answer
 */
TEST(test_write_answer, valid_answers)
{
        unsigned char data[2];
        int ret;

        data[0] = LOGGER_FRAME;
        data[1] = 42;
        ret = write_answer(data, 2);
        ASSERT_EQ(0, ret);
        ASSERT_STREQ("error 42\n", print_buff);

        data[0] = SET_TIME;
        data[1] = ACK;
        ret = write_answer(data, 2);
        ASSERT_EQ(0, ret);
        ASSERT_STREQ("set_time ACK\n", print_buff);

        data[0] = CONFIG_CONSUMPTION;
        data[1] = NACK;
        ret = write_answer(data, 2);
        ASSERT_EQ(0, ret);
        ASSERT_STREQ("config_consumption_measure NACK\n", print_buff);

        data[0] = CONFIG_RADIO_STOP;
        data[1] = ACK;
        ret = write_answer(data, 2);
        ASSERT_EQ(0, ret);
        ASSERT_STREQ("config_radio_stop ACK\n", print_buff);

        data[0] = CONFIG_RADIO_MEAS;
        data[1] = ACK;
        ret = write_answer(data, 2);
        ASSERT_EQ(0, ret);
        ASSERT_STREQ("config_radio_measure ACK\n", print_buff);

        /* leds */
        data[0] = GREEN_LED_ON;
        data[1] = ACK;
        ret = write_answer(data, 2);
        ASSERT_EQ(0, ret);
        ASSERT_STREQ("green_led_on ACK\n", print_buff);

        data[0] = GREEN_LED_BLINK;
        data[1] = ACK;
        ret = write_answer(data, 2);
        ASSERT_EQ(0, ret);
        ASSERT_STREQ("green_led_blink ACK\n", print_buff);


        /* test commands */
        data[0] = TEST_RADIO_PING_PONG;
        data[1] = ACK;
        ret = write_answer(data, 2);
        ASSERT_EQ(0, ret);
        ASSERT_STREQ("test_radio_ping_pong ACK\n", print_buff);

        data[0] = TEST_GPIO;
        data[1] = ACK;
        ret = write_answer(data, 2);
        ASSERT_EQ(0, ret);
        ASSERT_STREQ("test_gpio ACK\n", print_buff);

        data[0] = TEST_I2C2;
        data[1] = ACK;
        ret = write_answer(data, 2);
        ASSERT_EQ(0, ret);
        ASSERT_STREQ("test_i2c ACK\n", print_buff);

        data[0] = TEST_PPS;
        data[1] = ACK;
        ret = write_answer(data, 2);
        ASSERT_EQ(0, ret);
        ASSERT_STREQ("test_pps ACK\n", print_buff);

        data[0] = TEST_GOT_PPS;
        data[1] = ACK;
        ret = write_answer(data, 2);
        ASSERT_EQ(0, ret);
        ASSERT_STREQ("test_got_pps ACK\n", print_buff);

        data[0] = 0xFF;
        data[1] = ACK;
        ret = write_answer(data, 2);
        ASSERT_NE(0, ret);
}

TEST(test_write_answer, invalid_answers)
{
        unsigned char data[2];
        int ret;

        ret = write_answer(data, 1);
        ASSERT_EQ(-1, ret);

        data[0] = CONFIG_CONSUMPTION;
        data[1] = 42;
        ret = write_answer(data, 2);
        ASSERT_EQ(-3, ret);
}


/*
 *  Test parse_cmd
 */
TEST(test_parse_cmd, invalid_commands)
{
        int ret;
        struct command_buffer cmd_buff = {0};
        char cmd[256] = {0};

        strcpy(cmd, "");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_NE(0, ret);

        strcpy(cmd, "unkown_cmd with arg");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_NE(0, ret);

        strcpy(cmd, "config_consumption_measure blabla");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_NE(0, ret);

        strcpy(cmd, "test_radio_ping_pong");
        ret = parse_cmd(cmd, &cmd_buff);
        ASSERT_NE(0, ret);
}

TEST(test_cstrtok, test)
{
    char *token;

    token = cstrtok("0123456789ABCDEF0123456789ABCDEF01  lala");
    ASSERT_EQ(NULL, token);

    token = cstrtok("0123");
    ASSERT_STREQ("0123", token);

    token = cstrtok("abcd 0123");
    ASSERT_STREQ("abcd", token);
}

/*
 * Test thread (for coverage)
 */
TEST(test_thread, start_thread)
{
        int ret;

        ret = command_reader_start(42);
        ASSERT_EQ(0, ret);
}


