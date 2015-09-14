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
