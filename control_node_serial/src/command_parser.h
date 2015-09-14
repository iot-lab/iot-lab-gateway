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
