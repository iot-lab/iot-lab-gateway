#include <gtest/gtest.h>
#include "command_reader.c"

// Don't want to mock these
#include "utils.c"
#include "time_update.c"


#include <unistd.h> // sleep, size_t

/* Mock EXTERNAL dependency functions
 * with function definition
 * */

static int write_called = 0;

ssize_t write(int fd, const void *buf, size_t count)
{
        write_called++;
        return count;
}



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

        char config_4_cmd[] = "config_consumption_measure start 3.3V p 1 v 1 c 1 -p 8244us -a 1024";
        ret = parse_cmd(config_4_cmd, &cmd_buff);
        ASSERT_EQ(0, ret);
        ASSERT_NE(payload_1_2, cmd_buff.u.s.payload[2] << 8 | cmd_buff.u.s.payload[1]);
}



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







// For coverage
TEST(test_thread, start_thread)
{
        int ret;

        ret = command_reader_start(42);
        ASSERT_EQ(0, ret);
}


