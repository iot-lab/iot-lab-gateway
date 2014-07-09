#ifndef COMMAND_PARSER_H
#define COMMAND_PARSER_H

#include <stdint.h>

struct command_description;
typedef int (*cmd_fct_t)(char *, void *, void *);


struct command_description {
    char *fmt;
    uint8_t fmt_count;
    cmd_fct_t command;
};


struct command_description *command_parse(char *cmd,
        struct command_description *commands);

#endif//COMMAND_PARSER_H
