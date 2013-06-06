#include <unistd.h>

#include "common.h"
#include "serial.h"
#include "command_reader.h"

static char *tty_path = "/dev/ttyFITECO_GWT";

int main(int argc, char *argv[])
{
        (void) argc;
        (void) argv;

        int serial_fd = 0;

        if ((serial_fd = configure_tty(tty_path)) <= 0) {
                fprintf(stderr, "ERROR: Could not open and configure TTY %s\n", tty_path);
                close(serial_fd);
                return -1;
        }

        command_reader_start(serial_fd);
        pause();

        //start_listening(serial_fd, decode_pkt);

        return 0;
}
