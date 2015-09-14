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
#include "utils.c"


/* Mock EXTERNAL dependency functions
 * with function definition
 * */



/* Test values */
struct dict_entry example_d[] = {
        {"key1", 1},
        {"key2", 2},
        {"key3", 3},
        {NULL, 0},
};


TEST(dict_get_val_tests, get_valid_values)
{
        uint8_t value = 0;
        int ret;

        ret = get_val("key1", example_d, &value);
        ASSERT_EQ(0, ret);
        ASSERT_EQ((uint8_t) 1, value);

        ret = get_val("key3", example_d, &value);
        ASSERT_EQ(0, ret);
        ASSERT_EQ((uint8_t) 3, value);
}
TEST(dict_get_val_tests, get_unknown_value)
{
        uint8_t value = 0;
        int ret;

        ret = get_val("unkown_key", example_d, &value);
        ASSERT_NE(0, ret);
        ret = get_val(NULL, example_d, &value);
        ASSERT_NE(0, ret);
}


TEST(dict_get_key_tests, get_valid_keys)
{
        char *key = NULL;
        int ret;

        ret = get_key(1, example_d, &key);
        ASSERT_EQ(0, ret);
        ASSERT_STREQ("key1", key);

        ret = get_key(3, example_d, &key);
        ASSERT_EQ(0, ret);
        ASSERT_STREQ("key3", key);
}
TEST(dict_get_key_tests, get_uknown_keys)
{
        char *key = NULL;
        int ret;

        ret = get_key(42, example_d, &key);
        ASSERT_NE(0, ret);
}

