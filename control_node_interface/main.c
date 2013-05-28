#include <stdio.h>
#include <string.h>

#include <termios.h>
#include <unistd.h> // tcgetattr

#include <fcntl.h> // open

#include <errno.h>

#include <sys/param.h>

static const char *tty_path = "/dev/ttyFITECO_GWT";

// Documentation
// http://trainingkits.gweb.io/serial-linux.html
// http://en.wikibooks.org/wiki/Serial_Programming/Serial_Linux

static int configure_tty(int fd)
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


static struct pkt {
        unsigned int len;
        unsigned int missing;
        unsigned int current_len;
        unsigned char data[2048];
} current_pkt;




#define CONSUMPTION (0xFF)

static void decode_pkt()
{
        int num_measures = 0;

        unsigned int time;
        float t, p, v, c;

        unsigned char *current_pkt_index;

        static struct values {
                unsigned int time;
                float p;
                float v;
                float c;
        } current_values;



        switch (current_pkt.data[0]) {
                case 0:
                        break;
                case 1:
                        break;
                case 2:
                        break;
                case 3:
                        break;
                case 4:
                        break;
                case CONSUMPTION:
                        // 'FF 17 01 10 9C DC E4 3E 0A 62 91 40 4F 99 99 3D 2A 0D 65 '
                        // FF == conso, 17 == config
                        // 01 = num
                        num_measures      = current_pkt.data[2];
                        current_pkt_index = &current_pkt.data[3];

                        for (int i = 0; i < num_measures; i++) {
                                memcpy(&current_values, current_pkt_index, sizeof(current_values));
                                current_pkt_index += sizeof(current_values);

                                time = current_values.time;
                                t = time / ((float) 32768);
                                p = current_values.p;
                                v = current_values.v;
                                c = current_values.c;

                                printf("%f: %f %f %f\n", t, p, v, c);
                        }
                        break;
                default:
                        printf("ERROR unknown packet\n");
                        break;
        }
}


enum state_t {
        STATE_IDLE = 0,
        STATE_WAIT_LEN = 1,
        STATE_GET_PAYLOAD = 2,
        STATE_FULL = 3
};

unsigned char sync_byte = 0x80;

static void handle_packet(unsigned char *rx_buff, unsigned int len)
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
                                decode_pkt();

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


static void start_listening(int fd)
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

                /* printf("Read done: n_chars = %d\n", n_chars);

                for (int i = 0; i < n_chars; i++) {
                        printf("%02X\n", rx_buff[i]);
                } */
                handle_packet(rx_buff, n_chars);
        }


}


int main(int argc, char *argv[])
{
        (void) argc;
        (void) argv;

        int fd;

        fd = open(tty_path, O_RDWR | O_NOCTTY | O_NDELAY);
        if (fd == -1) {
                printf("ERROR: Could not open %s\n", tty_path);
                return -1;
        }
        if (configure_tty(fd)) {
                printf("ERROR: Could not configure TTY %s\n", tty_path);
                close(fd);
                return -1;
        }

        start_listening(fd);



        close(fd);

        return 0;
}
