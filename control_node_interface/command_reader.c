#include <pthread.h>
#include <stdio.h>

//#include <sys/types.h>
#include <signal.h>

#include "command_reader.h"
#include "constants.h"

struct dict_entry {
        char *str;
        unsigned char val;
};

struct dict_entry periods_d[] = {
        {"140us",  PERIOD_140us},
        {"204us",  PERIOD_204us},
        {"332us",  PERIOD_332us},
        {"588us",  PERIOD_588us},
        {"1100us", PERIOD_1100us},
        {"2116us", PERIOD_2116us},
        {"4156us", PERIOD_4156us},
        {"8244us", PERIOD_8244us},
};

struct dict_entry average_d[] = {
        {"1",    AVERAGE_1},
        {"4",    AVERAGE_4},
        {"16",   AVERAGE_16},
        {"64",   AVERAGE_64},
        {"128",  AVERAGE_128},
        {"256",  AVERAGE_256},
        {"512",  AVERAGE_512},
        {"1024", AVERAGE_1024},
};

struct dict_entry power_source_d[] = {
        {"3.3V",  SOURCE_3_3V},
        {"5V",    SOURCE_5V},
        {"BATT",  SOURCE_BATT},
};

int pthread_kill(pthread_t thread, int sig);   // implicit declaration ?

static void *read_commands(void *attr);


static struct {
        pthread_t reader_thread;

} reader_state;



int command_reader_start(int serial_fd)
{
        (void) serial_fd;

        pthread_create(&reader_state.reader_thread, NULL, read_commands, NULL);
        return 0;
}

int command_reader_stop()
{
        pthread_kill(reader_state.reader_thread, SIGINT);
        return 0;
}



static void *read_commands(void *attr)
{
        (void) attr;


        return NULL;
}





// getline
