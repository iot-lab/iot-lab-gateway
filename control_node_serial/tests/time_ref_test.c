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
