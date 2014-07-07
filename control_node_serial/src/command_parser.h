#ifndef COMMAND_PARSER_H
#define COMMAND_PARSER_H

#include <stdint.h>

struct command_description;
typedef int (*command_fct_t)(char *, void *, void *);


struct command_description {
    char *fmt;
    char *cmd_str;
    uint8_t fmt_count;
    command_fct_t command;
};


struct command_description *command_parse(char *cmd,
        struct command_description *commands);

#endif//COMMAND_PARSER_H
