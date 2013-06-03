#include <stdio.h>
#include <string.h>

#include <fcntl.h> // open
#include <unistd.h> // close

#include "protocol.h"
#include "serial.h"

static const char *tty_path = "/dev/ttyFITECO_GWT";

// Documentation
// http://trainingkits.gweb.io/serial-linux.html
// http://en.wikibooks.org/wiki/Serial_Programming/Serial_Linux



#define CONSUMPTION (0xFF)

static void decode_pkt(struct pkt *current_pkt)
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



        switch (current_pkt->data[0]) {
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
                        num_measures      = current_pkt->data[2];
                        current_pkt_index = &current_pkt->data[3];

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

        start_listening(fd, decode_pkt);

        close(fd);

        return 0;
}
