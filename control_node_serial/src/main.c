#include <unistd.h>
#include <stdio.h>

#include "common.h"
#include "serial.h"
#include "command_reader.h"
#include "decode.h"
#include "measures_handler.h"


int main(int argc, char *argv[])
{
        int serial_fd  = 0;
        unsigned char rx_buff[2048];
        char *tty_path = "/dev/ttyFITECO_GWT";
        int ret;


        // Get tty_path from arguments if available
        if (argc == 2)
                tty_path = argv[1];

        if ((serial_fd = configure_tty(tty_path)) <= 0) {
                PRINT_ERROR("Could not open and configure TTY %s\n", tty_path);
                close(serial_fd);
                return -1;
        }

        init_measures_handler();
        command_reader_start(serial_fd);
        do {
                ret = receive_data(serial_fd, rx_buff, sizeof(rx_buff),
                                decode_pkt);
        } while (ret > 0);
        PRINT_ERROR("Exit %s: Serial read returned %d\n", argv[0], ret);


        return 1;
}
