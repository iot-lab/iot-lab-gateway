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

#include <unistd.h>
#include <errno.h>
#include <stdio.h>
#include <ctype.h>
#include <stdlib.h>

#include "common.h"
#include "serial.h"
#include "command_reader.h"
#include "decode.h"
#include "measures_handler.h"
#include "sniffer_server.h"

#define TTY_PATH "/dev/ttyCN"


static void usage(char *program_name)
{
    PRINT_ERROR("Usage: %s [-d] [-t tty_path] [-c oml_config_file]\n",
            program_name);
    PRINT_ERROR("  %c: debug mode, print measures\n", 'd');
    PRINT_ERROR("  %c: Set tty path. Default %s\n", 't', TTY_PATH);
    PRINT_ERROR("  %c: OML config file path.\n", 'c');
}

int main(int argc, char *argv[])
{
    int serial_fd  = 0;
    unsigned char rx_buff[2048];
    int ret;


    int print_measures = 0;
    char *tty_path = TTY_PATH;
    char *oml_config_file_path = NULL;
    char c;
    opterr = 0;

    while ((c = getopt(argc, argv, "dt:c:")) != (char)-1) {
        switch (c) {
            case 'd':
                print_measures = 1;
                break;
            case 't':
                tty_path = optarg;
                break;
            case 'c':
                oml_config_file_path = optarg;
                break;
            case '?':
                if (optopt == 't' || optopt == 'c')
                    PRINT_ERROR("Option -%c requires an " \
                            "argument.\n", optopt);
                else if (isprint(optopt))
                    PRINT_ERROR("Unknown option `-%c`.\n", \
                            optopt);
                else
                    PRINT_ERROR("Unknown option character" \
                            "`\\x%x`.\n", optopt);
                usage(argv[0]);
                return EINVAL;
            default:
                usage(argv[0]);
                return EINVAL;
        }
    }

    if (0 >= (serial_fd = configure_tty(tty_path))) {
        PRINT_ERROR("Could not open and configure TTY %s\n", tty_path);
        close(serial_fd);
        return -1;
    }

    // measures and OML
    measures_handler_start(print_measures, oml_config_file_path);
    atexit(measures_handler_stop);

    // stdin parsing
    command_reader_start(serial_fd);
    // stdin parsing
    sniffer_server_start();

    // serial reader
    do {
        ret = receive_data(serial_fd, rx_buff, sizeof(rx_buff),
                decode_pkt);
    } while (ret > 0);
    PRINT_ERROR("Exit %s: Serial read returned %d\n", argv[0], ret);


    return 1;
}
