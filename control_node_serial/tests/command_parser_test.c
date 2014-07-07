#include <gtest/gtest.h>
#include <unistd.h> // sleep, size_t

#include "command_parser.c"

struct command_description commands[] = {
    {"no_arguments", "no_argument", 0, (command_fct_t) 1},
    {"one_argument %d", "one_argument", 1, (command_fct_t) 2},
    {"many_arguments %f lala %u test %s", "many_arguments", 3, (command_fct_t) 3},
    {NULL, NULL, 0, NULL}
};


TEST(test_command_parse, parse_different_commands)
{
    struct command_description *ret_fct;

    // Unkown
    ret_fct = command_parse("unknown_command", commands);
    ASSERT_EQ(NULL, ret_fct);

    // No arguments
    ret_fct = command_parse("no_arguments", commands);
    ASSERT_EQ(&commands[0], ret_fct);

    // One argument with valid value
    ret_fct = command_parse("one_argument 12", commands);
    ASSERT_EQ(&commands[1], ret_fct);
    // One argument without valid value
    ret_fct = command_parse("one_argument invalid", commands);
    ASSERT_EQ(NULL, ret_fct);


    // Test parsing multiple arguments
    ret_fct = command_parse("many_arguments 3.14 lala 42 test str", commands);
    ASSERT_EQ(&commands[2], ret_fct);
    // with invalid value
    ret_fct = command_parse("many_arguments 25 lala 1.414 test str", commands);
    ASSERT_EQ(NULL, ret_fct);
}

TEST(test_command_parse, too_big_number_of_arguments)
{
    struct command_description commands[] = {
        {"large_format_33"
            " %d %d %d %d %d %d %d %d"
            " %d %d %d %d %d %d %d %d"
            " %d %d %d %d %d %d %d %d"
            " %d %d %d %d %d %d %d %d"
            " %d", "large_format", 33, (command_fct_t) 1},
        {NULL, NULL, 0, NULL}
    };
    struct command_description *ret_fct;

    ret_fct = command_parse("large_format_33"
            " 1 2 3 4 5 6 7 8"
            " 9 10 11 12 13 14 15 16"
            " 17 18 19 20 21 22 23 24"
            " 25 26 27 28 29 30 31 32 33", commands);
    ASSERT_EQ(NULL, ret_fct);
}
