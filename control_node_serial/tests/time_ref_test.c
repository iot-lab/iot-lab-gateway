#include <gtest/gtest.h>
#include "time_ref.c"


TEST(test_timeval_substract, test_all_cases)
{
    struct timeval a, b, result;
    int ret;

    a.tv_sec  = 0;
    a.tv_usec = 0;
    b.tv_sec  = 0;
    b.tv_usec = 0;

    ret = timeval_substract(&result, &a, &b);
    ASSERT_GE(0, ret);
    ASSERT_EQ(0, result.tv_sec);
    ASSERT_EQ(0, result.tv_usec);

    a.tv_sec  = 0;
    a.tv_usec = 99;
    b.tv_sec  = 0;
    b.tv_usec = 100;
    ret = timeval_substract(&result, &a, &b);
    ASSERT_LT(0, ret);
    ASSERT_EQ(-1, result.tv_sec);
    ASSERT_EQ(999999, result.tv_usec);

    a.tv_sec  = 0;
    a.tv_usec = 10000000;
    b.tv_sec  = 0;
    b.tv_usec = 0;
    ret = timeval_substract(&result, &a, &b);
    ASSERT_GE(0, ret);
    ASSERT_EQ(10, result.tv_sec);
    ASSERT_EQ(0, result.tv_usec);













}
