#include <gtest/gtest.h>
#include <unistd.h> // sleep, size_t

/*
 * Mock log_print
 */

char print_buff[2048];
#define fprintf(stream, ...)  snprintf(print_buff, sizeof(print_buff), __VA_ARGS__)

#include "command_reader.c"


/* Mock EXTERNAL dependency functions
 * with function definition
 */
// Don't want to mock these
#include "utils.c"
#include "time_update.c"

static int write_called = 0;

ssize_t write(int fd, const void *buf, size_t count)
{
        write_called++;
        return count;
}



/*
 *  Test parse_cmd
 */
TEST(test_parse_cmd, simple_commands)
{
        int ret;
        struct command_buffer cmd_buff;

        char reset_cmd[] = "reset_time";
        ret = parse_cmd(reset_cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(1, cmd_buff.u.s.len);
        ASSERT_EQ(RESET_TIME, cmd_buff.u.s.payload[0]);

        char start_cmd[] = "start dc";
        ret = parse_cmd(start_cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(2, cmd_buff.u.s.len);
        ASSERT_EQ(OPEN_NODE_START, cmd_buff.u.s.payload[0]);

        char stop_cmd[] = "stop battery";
        ret = parse_cmd(stop_cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(2, cmd_buff.u.s.len);
        ASSERT_EQ(OPEN_NODE_STOP, cmd_buff.u.s.payload[0]);
}

TEST(test_parse_cmd, consumption)
{
        /*
         * Sending multiple config_consumption_measure commands
         * and checking that the configuration is different each time
         */
        int ret;
        struct command_buffer cmd_buff;

        char config_0_cmd[] = "config_consumption_measure stop";
        ret = parse_cmd(config_0_cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(3, cmd_buff.u.s.len);
        ASSERT_EQ(CONFIG_POWER_POLL, cmd_buff.u.s.payload[0]);
        ASSERT_EQ(0, cmd_buff.u.s.payload[2]);

        char config_1_cmd[] = "config_consumption_measure start 3.3V p 1 v 1 c 1 -p 140us -a 1";
        ret = parse_cmd(config_1_cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(3, cmd_buff.u.s.len);
        ASSERT_EQ(CONFIG_POWER_POLL, cmd_buff.u.s.payload[0]);
        ASSERT_EQ(CONSUMPTION_START,
                        (cmd_buff.u.s.payload[2] | CONSUMPTION_START));
        unsigned payload_1_2 = cmd_buff.u.s.payload[2] << 8 | cmd_buff.u.s.payload[1];

        char config_2_cmd[] = "config_consumption_measure start BATT p 1 v 1 c 1 -p 140us -a 1";
        ret = parse_cmd(config_2_cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_NE(payload_1_2, cmd_buff.u.s.payload[2] << 8 | cmd_buff.u.s.payload[1]);

        char config_3_cmd[] = "config_consumption_measure start 3.3V p 0 v 1 c 0 -p 140us -a 1";
        ret = parse_cmd(config_3_cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_NE(payload_1_2, cmd_buff.u.s.payload[2] << 8 | cmd_buff.u.s.payload[1]);
        char config_4_cmd[] = "config_consumption_measure start 3.3V p 1 v 0 c 1 -p 140us -a 1";
        ret = parse_cmd(config_4_cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_NE(payload_1_2, cmd_buff.u.s.payload[2] << 8 | cmd_buff.u.s.payload[1]);

        char config_5_cmd[] = "config_consumption_measure start 3.3V p 1 v 1 c 1 -p 8244us -a 1024";
        ret = parse_cmd(config_5_cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_NE(payload_1_2, cmd_buff.u.s.payload[2] << 8 | cmd_buff.u.s.payload[1]);
}


/*
 *  Test write_answer
 */
TEST(test_write_answer, valid_answers)
{
        unsigned char data[2];
        int ret;

        data[0] = ERROR_FRAME;
        data[1] = 42;
        ret = write_answer(data, 2);
        ASSERT_EQ(0, ret);
        ASSERT_STREQ("error 42\n", print_buff);

        data[0] = RESET_TIME;
        data[1] = ACK;
        ret = write_answer(data, 2);
        ASSERT_EQ(0, ret);
        ASSERT_STREQ("reset_time ACK\n", print_buff);

        data[0] = CONFIG_POWER_POLL;
        data[1] = NACK;
        ret = write_answer(data, 2);
        ASSERT_EQ(0, ret);
        ASSERT_STREQ("config_consumption_measure NACK\n", print_buff);
}

TEST(test_write_answer, invalid_answers)
{
        unsigned char data[2];
        int ret;

        ret = write_answer(data, 1);
        ASSERT_EQ(-1, ret);

        data[0] = MEASURES_FRAME_MASK;
        ret = write_answer(data, 2);
        ASSERT_EQ(-2, ret);

        data[0] = CONFIG_POWER_POLL;
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
        struct command_buffer cmd_buff;

        char empty[] = "";
        ret = parse_cmd(empty, &cmd_buff);
        ASSERT_EQ(1, ret);

        char unkown[] = "unkown_cmd with arg";
        ret = parse_cmd(unkown, &cmd_buff);
        ASSERT_EQ(1, ret);

        char consumption[] = "config_consumption_measure blabla";
        ret = parse_cmd(consumption, &cmd_buff);
        ASSERT_EQ(1, ret);
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


