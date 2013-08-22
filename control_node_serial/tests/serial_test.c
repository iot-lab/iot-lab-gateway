#include <gtest/gtest.h>
#include <unistd.h>

#include "mock_fprintf.h"  // include before other includes

#include "serial.c"


/*
 * mock external function
 */

static ssize_t read_ret = 0;
ssize_t read(int fd, void *buf, size_t count)
{
        return read_ret;
}
TEST(receive_data, bad_return_value_for_read)
{
        int ret;
        errno = 0;
        read_ret = -1;
        ret = receive_data(0, NULL, 0, NULL);
        ASSERT_EQ(-1, ret);

        read_ret = 0;
        ret = receive_data(0, NULL, 0, NULL);
        ASSERT_EQ(0, ret);
}


// for coverage
TEST(parse_rx_data, case_default_coverage)
{
        state = (state_t) 42; // unkown state
        unsigned char rx_buff[1];
        rx_buff[0] = sync_byte;

        parse_rx_data(rx_buff, 1, NULL);
        // got out and read rx_byte
        ASSERT_EQ(STATE_WAIT_LEN, state);
}




static int open_ret = -1;
int open(const char *pathname, int flags)
{
        return open_ret;
};

static int tcflush_ret = -1;
int tcflush(int fd, int queue_selector)
{
        return tcflush_ret;
}

static int tcgetattr_ret = 1;
int tcgetattr(int fd, struct termios *termios_p)
{
        return tcgetattr_ret;
}

void cfmakeraw(struct termios *termios_p);
static int cfsetspeed_ret = 1;
int cfsetspeed(struct termios *termios_p, speed_t speed)
{
        return cfsetspeed_ret;

}

static int tcsetattr_ret = -1;
int tcsetattr(int fd, struct termios *termios_p)
{
        return tcsetattr_ret;
}


TEST(configure_tty, all_error_cases)
{
        int ret;
        // error on open
        ret = configure_tty(NULL);
        ASSERT_EQ(-1, ret);


        open_ret = 42;
        // error on tcflush
        ret = configure_tty("utils/dummy_tty_for_tests");
        ASSERT_EQ(-2, ret);

        tcflush_ret = 0;
        // error on tcgetattr
        ret = configure_tty("utils/dummy_tty_for_tests");
        ASSERT_EQ(-3, ret);

        tcgetattr_ret = 0;
        // error on cfsetspeed
        ret = configure_tty("utils/dummy_tty_for_tests");
        ASSERT_EQ(-4, ret);

        cfsetspeed_ret = 0;
        // error on tcsetattr_ret
        ret = configure_tty("utils/dummy_tty_for_tests");
        ASSERT_EQ(-5, ret);
}



