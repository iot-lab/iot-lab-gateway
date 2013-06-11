#include <unistd.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

#include "constants.h"
#include "common.h"
#include "serial.h"
#include "command_reader.h"
#include "measures_handler.h"

static char *tty_path = "/dev/ttyFITECO_GWT";

static void decode_pkt(struct pkt *current_pkt)
{
        uint8_t pkt_type = current_pkt->data[0];

#if DEBUG
        for (uint8_t i=0; i < current_pkt->len; i++) {
                DEBUG_PRINT(" %02X", current_pkt->data[i]);
        }
        DEBUG_PRINT("\n");
#endif

        if ((pkt_type & MEASURES_FRAME_MASK) == MEASURES_FRAME_MASK) {
                // send to measures packets handler
                handle_measure_pkt(current_pkt->data, current_pkt->len);
        } else {
                // answer commands
                write_answer(current_pkt->data, current_pkt->len);
        }
}

int main(int argc, char *argv[])
{
        (void) argc;
        (void) argv;

        int serial_fd = 0;

        if ((serial_fd = configure_tty(tty_path)) <= 0) {
                fprintf(LOG, "ERROR: Could not open and configure TTY %s\n", tty_path);
                close(serial_fd);
                return -1;
        }

        command_reader_start(serial_fd);

        start_listening(serial_fd, decode_pkt);

        return 0;
}
