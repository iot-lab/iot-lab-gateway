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

        char config_1_cmd[] = "config_consumption_measure start 3.3V p 1 v 1 c 1 -p 140 -a 1";
        ret = parse_cmd(config_1_cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(3, cmd_buff.u.s.len);
        ASSERT_EQ(CONFIG_POWER_POLL, cmd_buff.u.s.payload[0]);
        ASSERT_EQ(CONSUMPTION_START,
                        (cmd_buff.u.s.payload[2] | CONSUMPTION_START));
        unsigned payload_1_2 = cmd_buff.u.s.payload[2] << 8 | cmd_buff.u.s.payload[1];

        char config_2_cmd[] = "config_consumption_measure start BATT p 1 v 1 c 1 -p 140 -a 1";
        ret = parse_cmd(config_2_cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_NE(payload_1_2, cmd_buff.u.s.payload[2] << 8 | cmd_buff.u.s.payload[1]);

        char config_3_cmd[] = "config_consumption_measure start 3.3V p 0 v 1 c 0 -p 140 -a 1";
        ret = parse_cmd(config_3_cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_NE(payload_1_2, cmd_buff.u.s.payload[2] << 8 | cmd_buff.u.s.payload[1]);
        char config_4_cmd[] = "config_consumption_measure start 3.3V p 1 v 0 c 1 -p 140 -a 1";
        ret = parse_cmd(config_4_cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_NE(payload_1_2, cmd_buff.u.s.payload[2] << 8 | cmd_buff.u.s.payload[1]);

        char config_5_cmd[] = "config_consumption_measure start 3.3V p 1 v 1 c 1 -p 8244 -a 1024";
        ret = parse_cmd(config_5_cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_NE(payload_1_2, cmd_buff.u.s.payload[2] << 8 | cmd_buff.u.s.payload[1]);
}

TEST(test_parse_cmd, radio_signal)
{
        /*
         * Sending multiple config_consumption_measure commands
         * and checking that the configuration is different each time
         */
        int ret;
        struct command_buffer cmd_buff;

        char config_0_cmd[] = "config_radio_signal 3 26";
        ret = parse_cmd(config_0_cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(3, cmd_buff.u.s.len);
        ASSERT_EQ(CONFIG_RADIO, cmd_buff.u.s.payload[0]);
        ASSERT_EQ(POWER_3dBm, cmd_buff.u.s.payload[1]);
        ASSERT_EQ(26, cmd_buff.u.s.payload[2]);

        char config_1_cmd[] = "config_radio_signal -723 26";
        ret = parse_cmd(config_1_cmd, &cmd_buff);
        ASSERT_NE(0, ret);
        char config_2_cmd[] = "config_radio_signal -17 28";
        ret = parse_cmd(config_2_cmd, &cmd_buff);
        ASSERT_NE(0, ret);
        char config_3_cmd[] = "config_radio_signal -17 3";
        ret = parse_cmd(config_3_cmd, &cmd_buff);
        ASSERT_NE(0, ret);
}

TEST(test_parse_cmd, radio_measure)
{
        /*
         * Sending multiple config_consumption_measure commands
         * and checking that the configuration is different each time
         */
        int ret;
        struct command_buffer cmd_buff;

        char config_0_cmd[] = "config_radio_measure start 42";
        ret = parse_cmd(config_0_cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(4, cmd_buff.u.s.len);
        ASSERT_EQ(CONFIG_RADIO_POLL, cmd_buff.u.s.payload[0]);
        ASSERT_EQ(RADIO_START, cmd_buff.u.s.payload[1]);
        ASSERT_EQ(42, cmd_buff.u.s.payload[2]);
        ASSERT_EQ(0, cmd_buff.u.s.payload[3]);

        char config_1_cmd[] = "config_radio_measure start 256";
        ret = parse_cmd(config_1_cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(4, cmd_buff.u.s.len);
        ASSERT_EQ(CONFIG_RADIO_POLL, cmd_buff.u.s.payload[0]);
        ASSERT_EQ(RADIO_START, cmd_buff.u.s.payload[1]);
        ASSERT_EQ(0, cmd_buff.u.s.payload[2]);
        ASSERT_EQ(1, cmd_buff.u.s.payload[3]);


        char config_2_cmd[] = "config_radio_measure stop";
        ret = parse_cmd(config_2_cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(4, cmd_buff.u.s.len);
        ASSERT_EQ(CONFIG_RADIO_POLL, cmd_buff.u.s.payload[0]);
        ASSERT_EQ(RADIO_STOP, cmd_buff.u.s.payload[1]);
        ASSERT_EQ(0, cmd_buff.u.s.payload[2]);
        ASSERT_EQ(0, cmd_buff.u.s.payload[3]);



        char config_3_cmd[] = "config_radio_measure not_valid";
        ret = parse_cmd(config_3_cmd, &cmd_buff);
        ASSERT_NE(0, ret);

        // min to 2
        char config_4_cmd[] = "config_radio_measure start 1";
        ret = parse_cmd(config_4_cmd, &cmd_buff);
        ASSERT_NE(0, ret);
        // max to 499
        char config_5_cmd[] = "config_radio_measure start 500";
        ret = parse_cmd(config_5_cmd, &cmd_buff);
        ASSERT_NE(0, ret);
}


TEST(test_parse_cmd, test_commands)
{
        int ret;
        struct command_buffer cmd_buff;

        // ping pong
        char ping_pong_start[] = "test_radio_ping_pong start";
        ret = parse_cmd(ping_pong_start, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(2, cmd_buff.u.s.len);
        ASSERT_EQ(TEST_RADIO_PING_PONG, cmd_buff.u.s.payload[0]);

        // ping pong
        char ping_pong_stop[] = "test_radio_ping_pong stop";
        ret = parse_cmd(ping_pong_stop, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_EQ(2, cmd_buff.u.s.len);
        ASSERT_EQ(TEST_RADIO_PING_PONG, cmd_buff.u.s.payload[0]);
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

        data[0] = CONFIG_RADIO;
        data[1] = ACK;
        ret = write_answer(data, 2);
        ASSERT_EQ(0, ret);
        ASSERT_STREQ("config_radio_signal ACK\n", print_buff);

        data[0] = CONFIG_RADIO_POLL;
        data[1] = ACK;
        ret = write_answer(data, 2);
        ASSERT_EQ(0, ret);
        ASSERT_STREQ("config_radio_measure ACK\n", print_buff);


        data[0] = TEST_RADIO_PING_PONG;
        data[1] = ACK;
        ret = write_answer(data, 2);
        ASSERT_EQ(0, ret);
        ASSERT_STREQ("test_radio_ping_pong ACK\n", print_buff);
}

TEST(test_write_answer, invalid_answers)
{
        unsigned char data[2];
        int ret;

        ret = write_answer(data, 1);
        ASSERT_EQ(-1, ret);

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
        ASSERT_NE(0, ret);

        char unkown[] = "unkown_cmd with arg";
        ret = parse_cmd(unkown, &cmd_buff);
        ASSERT_NE(0, ret);

        char consumption[] = "config_consumption_measure blabla";
        ret = parse_cmd(consumption, &cmd_buff);
        ASSERT_NE(0, ret);

        char radio_ping_pong[] = "test_radio_ping_pong";
        ret = parse_cmd(radio_ping_pong, &cmd_buff);
        ASSERT_NE(0, ret);
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


