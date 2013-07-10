#include <unistd.h>
#include <stdio.h>

#include "common.h"
#include "serial.h"
#include "command_reader.h"
#include "decode.h"


int main(int argc, char *argv[])
{
        int serial_fd  = 0;
        char *tty_path = "/dev/ttyFITECO_GWT";


        // Get tty_path from arguments if available
        if (argc == 2)
                tty_path = argv[1];

        if ((serial_fd = configure_tty(tty_path)) <= 0) {
                fprintf(LOG, "ERROR: Could not open and configure TTY %s\n", tty_path);
                close(serial_fd);
                return -1;
        }

        command_reader_start(serial_fd);
        start_listening(serial_fd, decode_pkt);

        return 0;
}
