#include <stdio.h>
#include <string.h>

#include <termios.h>
#include <unistd.h> // tcgetattr
#include <fcntl.h>  // open, fcntl

#include <errno.h>
#include <sys/param.h> // MIN


#include "serial.h"

static void parse_rx_data(unsigned char *rx_buff, unsigned int len,
                void (*handle_pkt)(struct pkt*));
static const unsigned char sync_byte = 0x80;


struct pkt current_pkt;

int configure_tty(int fd)
{
        int ret = 0;
        struct termios tty;
        memset(&tty, 0, sizeof(tty));

        if (tcgetattr(fd, &tty)) {
                perror("Error in tcgetattr");
                return -1;
        }

        cfsetospeed(&tty, B500000);
        cfsetispeed(&tty, B500000);

        tty.c_cc[VMIN]  = 1; // blocking mode, should read at least 1 char


        if (tcsetattr(fd, TCSANOW, &tty) == -1) {
                perror("Could not set attribute to tty");
                return -1;
        }

        if (fcntl(fd, F_SETFL, 0)) {
                printf("fcntl failed\n");
        }

        // maybe redo a get and check that it worked (see tcsetattr manpage)

        return ret;
}



void start_listening(int fd, void (*handle_pkt)(struct pkt*))
{
        unsigned char rx_buff[2048];
        int n_chars = 0;
        int err;

        while (1) {
                n_chars = 0;

                while (n_chars <= 0) {
                        n_chars = read(fd, rx_buff, sizeof(rx_buff));
                        printf("n_chars %d\n", n_chars);
                        if (n_chars == -1) {
                                err = errno;
                                printf("Error %d: %s\n", err, strerror(err));
                        }
                }
                parse_rx_data(rx_buff, n_chars, handle_pkt);
        }


}


enum state_t {
        STATE_IDLE = 0,
        STATE_WAIT_LEN = 1,
        STATE_GET_PAYLOAD = 2,
        STATE_FULL = 3
};

static void parse_rx_data(unsigned char *rx_buff, unsigned int len, void (*handle_pkt)(struct pkt*))
{
        static enum state_t current_state = STATE_IDLE;

        unsigned int cur_idx   = 0;
        unsigned int remaining = len;
        unsigned char *sync_byte_addr;
        unsigned int num_bytes;

        while (remaining > 0 || current_state == STATE_FULL) {
                switch (current_state) {
                        case STATE_IDLE:
                                sync_byte_addr = memchr(&rx_buff[cur_idx], sync_byte, remaining);
                                if (sync_byte_addr == NULL) {
                                        // Not found
                                        cur_idx   = len;
                                        remaining = 0;
                                } else {
                                        // cur_idx -> sync_byte
                                        cur_idx = sync_byte_addr - rx_buff; // size_t
                                        // process sync_byte
                                        cur_idx++;
                                        remaining = len - cur_idx;
                                        current_state = STATE_WAIT_LEN;
                                }
                                break;
                        case STATE_WAIT_LEN:
                                current_pkt.len         = rx_buff[cur_idx];
                                current_pkt.missing     = current_pkt.len;
                                current_pkt.current_len = 0;

                                cur_idx++;
                                remaining = len - cur_idx;

                                current_state = STATE_GET_PAYLOAD;
                                break;
                        case STATE_GET_PAYLOAD:
                                num_bytes = MIN(current_pkt.missing, remaining);

                                memcpy(&current_pkt.data[current_pkt.current_len], &rx_buff[cur_idx], num_bytes);

                                // update pkt
                                current_pkt.missing     -= num_bytes;
                                current_pkt.current_len += num_bytes;
                                // update current buffer status
                                cur_idx                 += num_bytes;
                                remaining               -= num_bytes;


                                if (current_pkt.missing == 0) {
                                        current_state = STATE_FULL;
                                } // else same state

                                break;
                        case STATE_FULL:
                                printf("got packet with length: %d\n'", current_pkt.len);
                                handle_pkt(&current_pkt);

                                current_pkt.len = 0;
                                current_pkt.missing = 0;
                                current_pkt.current_len = 0;

                                current_state = STATE_IDLE;
                                break;
                        default:
                                break;
                }
        }
}
