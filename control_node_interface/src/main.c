#include <unistd.h>

#include "command_reader.h"

int main(int argc, char *argv[])
{
        (void) argc;
        (void) argv;


        int serial_fd = 0;
        command_reader_start(serial_fd);
        pause();

        return 0;
}
