// getline (for glibc > 2.10)
#define _POSIX_C_SOURCE  200809L

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <pthread.h>

#include "command_reader.h"
#include "constants.h"

#include "common.h"

struct dict_entry {
        char *str;
        unsigned char val;
};
struct command_buffer {
        union {
                struct {
                        unsigned char sync;
                        unsigned char len;
                        unsigned char payload[256];
                };
                unsigned char pkt[258];
        };
};

static int get_val(char *key, struct dict_entry dict[], uint8_t *val)
{
        if (!key)
                return -1;
        size_t i = 0;
        while (dict[i].str != NULL) {
                if (!strcmp(dict[i].str, key)) {
                        *val = dict[i].val;
                        return 0;
                }
                i++;
        }
        return -1;
}

struct dict_entry alim_d[] = {
        {"dc", DC},
        {"battery", BATTERY},
        {NULL, 0},
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
        {NULL, 0},
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
        {NULL, 0},
};

struct dict_entry power_source_d[] = {
        {"3.3V",  SOURCE_3_3V},
        {"5V",    SOURCE_5V},
        {"BATT",  SOURCE_BATT},
        {NULL, 0},
};

static void *read_commands(void *attr);

static struct state {
        int       serial_fd;
} reader_state;


int command_reader_start(int serial_fd)
{
        int ret;
        pthread_t reader_thread;

        reader_state.serial_fd = serial_fd;
        ret = pthread_create(&reader_thread, NULL, read_commands, &reader_state);
        return ret;
}


static int parse_cmd(char *line_buff, struct command_buffer *cmd_buff)
{
        char *command = NULL;
        char *arg = NULL;

        unsigned char frame_type = 0;
        unsigned char val = 0;
        int got_error = 0;


        cmd_buff->sync = SYNC_BYTE;
        cmd_buff->len  = 0;
        memset(&cmd_buff->payload, 0, sizeof(cmd_buff->payload));


        command = strtok(line_buff, " ");
        if (!command) {
                return 1; //empty lines
        }


        if (strcmp(command, "reset_time") == 0) {
                frame_type = RESET_TIME;
                cmd_buff->payload[cmd_buff->len++] = frame_type;

        } else if (strcmp(command, "start") == 0) {
                frame_type = OPEN_NODE_START;
                cmd_buff->payload[cmd_buff->len++] = frame_type;

                // DC BATT
                arg = strtok(NULL, " ");
                got_error |= get_val(arg, alim_d, &val);
                cmd_buff->payload[cmd_buff->len++] = val;

        } else if (strcmp(command, "stop") == 0) {
                frame_type = OPEN_NODE_STOP;
                cmd_buff->payload[cmd_buff->len++] = frame_type;

                // DC BATT
                arg = strtok(NULL, " ");
                got_error |= get_val(arg, alim_d, &val);
                cmd_buff->payload[cmd_buff->len++] = val;

        } else if (strcmp(command, "consumption") == 0) {
                frame_type = CONFIG_POWER_POLL;
                cmd_buff->payload[cmd_buff->len++] = frame_type;

                // start stop
                arg = strtok(NULL, " ");
                if (strcmp(arg, "stop") == 0) {
                        // measures | source
                        // empty when 'stop'
                        cmd_buff->len++;
                        // status | period | average
                        cmd_buff->payload[cmd_buff->len] |= CONSUMPTION_STOP;
                        cmd_buff->len++;
                } else if (strcmp(arg, "start") == 0) {


                        // measures | source
                        // Source
                        arg = strtok(NULL, " ");
                        got_error |= get_val(arg, power_source_d, &val);
                        cmd_buff->payload[cmd_buff->len] |= val;
                        // Power
                        arg = strtok(NULL, " ");
                        got_error |= strcmp(arg, "p");
                        arg = strtok(NULL, " ");
                        if (atoi(arg))
                                cmd_buff->payload[cmd_buff->len] |= MEASURE_POWER;
                        // Voltage
                        arg = strtok(NULL, " ");
                        got_error |= strcmp(arg, "v");
                        arg = strtok(NULL, " ");
                        if (atoi(arg))
                                cmd_buff->payload[cmd_buff->len] |= MEASURE_VOLTAGE;
                        // Current
                        arg = strtok(NULL, " ");
                        got_error |= strcmp(arg, "c");
                        arg = strtok(NULL, " ");
                        if (atoi(arg))
                                cmd_buff->payload[cmd_buff->len] |= MEASURE_CURRENT;

                        cmd_buff->len++;


                        // status | period | average
                        cmd_buff->payload[cmd_buff->len] |= CONSUMPTION_START;
                        // period
                        arg = strtok(NULL, " ");
                        got_error |= strcmp(arg, "-p");
                        arg = strtok(NULL, " ");
                        got_error |= get_val(arg, periods_d, &val);
                        cmd_buff->payload[cmd_buff->len] |= val;


                        // average
                        arg = strtok(NULL, " ");
                        got_error |= strcmp(arg, "-a");
                        arg = strtok(NULL, " ");
                        got_error |= get_val(arg, average_d, &val);
                        cmd_buff->payload[cmd_buff->len] |= val;

                        cmd_buff->len++;

                } else {
                        got_error |= 1;
                }
        } else {
                got_error = 1;
        }

        arg = strtok(NULL, " ");
        while (arg != NULL) {
                got_error |= 1;
                DEBUG_PRINT("  '%s'\n", arg);
                arg = strtok(NULL, " ");
        }
        return got_error;
}



static void *read_commands(void *attr)
{
        struct state *reader_state = (struct state *) attr;
        (void) reader_state;

        struct command_buffer cmd_buff;
        size_t buff_size = 2048;
        char *line_buff  = malloc(buff_size);
        int ret;

        int n;
        while ((n = getline(&line_buff, &buff_size, stdin)) != -1) {
                line_buff[n - 1] = '\0'; // remove new line
                DEBUG_PRINT("Command: %s: ", line_buff);
                ret = parse_cmd(line_buff, &cmd_buff);
                if (ret) {
                        DEBUG_PRINT("Error parsing\n");
                } else {
                        DEBUG_PRINT("\n\t");
                        for (int i=0; i < 2 + cmd_buff.len; i++) {
                                DEBUG_PRINT(" %02X", cmd_buff.pkt[i]);
                        }
                        DEBUG_PRINT("\n");
                }
        }
        return NULL;
}


