#include <stdio.h>
#include <string.h>

#include <termios.h>
#include <unistd.h> // tcgetattr

#include <fcntl.h> // open

#include <errno.h>

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

        cfsetspeed(&tty, B500000);
        tty.c_cc[VMIN]  = 1; // blocking mode, should read at least 1 char
        tty.c_cc[VTIME] = 1; // timeout 0.1s (deciseconds)


        if (tcsetattr(fd, TCSANOW, &tty) == -1) {
                perror("Could not set attribute to tty");
                return -1;
        }

        // maybe redo a get and check that it worked (see tcsetattr manpage)

        return ret;
}


int main(int argc, char *argv[])
{
        (void) argc;
        (void) argv;

        int fd;
        char rx_buff[2048];

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

        int n_chars = read(fd, rx_buff, sizeof(rx_buff));

        close(fd);

        return 0;
}
