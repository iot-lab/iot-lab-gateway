#define _POSIX_C_SOURCE  200809L
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

#define TTY_PATH "/dev/ttyFITECO_GWT"


int main(int argc, char *argv[])
{
        int serial_fd  = 0;
        unsigned char rx_buff[2048];
        int ret;


        int print_measures = 0;
        char *tty_path = TTY_PATH;
        char c;
        opterr = 0;

        while ((c = getopt(argc, argv, "dt:")) != (char)-1) {
                switch (c) {
                        case 't':
                                tty_path = optarg;
                                break;
                        case 'd':
                                print_measures = 1;
                                break;
                        case '?':
                                if (optopt == 't')
                                        PRINT_ERROR("Option -%c requires an " \
                                                    "argument.\n", optopt);
                                else if (isprint(optopt))
                                        PRINT_ERROR("Unknown option `-%c`.\n", \
                                                    optopt);
                                else
                                        PRINT_ERROR("Unknown option character" \
                                                    "`\\x%x`.\n", optopt);
                                PRINT_ERROR("Usage: %s [-d] [-t tty_path]\n", argv[0]);
                                PRINT_ERROR("  %c: debug mode, print measures\n", 'd');
                                PRINT_ERROR("  %c: Set tty path. Default %s\n", 't', TTY_PATH);
                                return EINVAL;
                        default:
                                abort();
                }
        }


        if ((serial_fd = configure_tty(tty_path)) <= 0) {
                PRINT_ERROR("Could not open and configure TTY %s\n", tty_path);
                close(serial_fd);
                return -1;
        }

        init_measures_handler(print_measures);
        command_reader_start(serial_fd);
        do {
                ret = receive_data(serial_fd, rx_buff, sizeof(rx_buff),
                                decode_pkt);
        } while (ret > 0);
        PRINT_ERROR("Exit %s: Serial read returned %d\n", argv[0], ret);


        return 1;
}
