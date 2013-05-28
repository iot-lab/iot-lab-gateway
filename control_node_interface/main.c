#include <stdio.h>

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

        if (tcgetattr(fd, &tty)) {
                perror("Error in tcgetattr");
                return -1;
        }

        return ret;
}


int main(int argc, char *argv[])
{
        (void) argc;
        (void) argv;
        int fd;

        printf("Lala\n");
        fd = open(tty_path, O_RDWR | O_NOCTTY | O_NDELAY);
        if (fd == -1) {
                printf("ERROR: Could not open %s\n", tty_path);
        }

        return 0;
}
