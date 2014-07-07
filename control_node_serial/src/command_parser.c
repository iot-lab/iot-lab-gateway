#include <stdio.h>
#include <string.h>

#include "common.h"
#include "command_parser.h"


struct command_description *command_parse(char *cmd,
        struct command_description *commands)
{
    struct command_description *cur;
    char buff[256];

    for (size_t i = 0; cur = &commands[i], cur->fmt != NULL; i++) {
        // No format to parse, only string comparison
        if (cur->fmt_count == 0) {
            if (strcmp(cmd, cur->fmt) == 0)
                return cur;
            continue;
        }

        // not handling more than 32 arguments
        if (cur->fmt_count > 32) {
            PRINT_ERROR("Too many arguments to parse: %u > max(32)\n",
                    cur->fmt_count);
            continue;
        }
        // set 32 times 'buff' as arguments buffer
        int ret = sscanf(cmd, cur->fmt,
                buff, buff, buff, buff, buff, buff, buff, buff,
                buff, buff, buff, buff, buff, buff, buff, buff,
                buff, buff, buff, buff, buff, buff, buff, buff,
                buff, buff, buff, buff, buff, buff, buff, buff);
        if (ret == (int)cur->fmt_count)
            return cur;
    }
    return NULL;
}
