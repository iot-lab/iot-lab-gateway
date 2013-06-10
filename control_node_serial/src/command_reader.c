// getline (for glibc > 2.10)
#define _POSIX_C_SOURCE  200809L

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/time.h>

#include <pthread.h>
#include "common.h"

#include "command_reader.h"
#include "constants.h"
#include "time_update.h"


struct dict_entry {
        char *str;
        unsigned char val;
};
struct command_buffer {
        union {
                struct _pkt{
                        unsigned char sync;
                        unsigned char len;
                        unsigned char payload[256];
                } s;
                unsigned char pkt[258];
        } u;
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
static int get_key(uint8_t val, struct dict_entry dict[], char **key)
{
        if (!key)
                return -1;
        size_t i = 0;
        while (dict[i].str != NULL) {
                if (val == dict[i].val) {
                        *key = dict[i].str;
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


/* dict used for answers, to translate code to string */

struct dict_entry answers_d[] = {
        {"error", ERROR_FRAME},
        {"start", OPEN_NODE_START},
        {"stop", OPEN_NODE_STOP},
        {"reset_time", RESET_TIME},

        {"config_radio", CONFIG_RADIO},
        {"config_radio_measure", CONFIG_RADIO_POLL},
        {"config_radio_noise", CONFIG_RADIO_NOISE},
        {"config_radio_sniffer", CONFIG_SNIFFER},

        {"config_fake_sensor", CONFIG_SENSOR},

        {"config_consumption_measure", CONFIG_POWER_POLL},
        {NULL, 0},
};


struct dict_entry ack_d[] = {
        {"ACK", ACK},
        {"NACK", NACK},
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


        cmd_buff->u.s.sync = SYNC_BYTE;
        cmd_buff->u.s.len  = 0;
        memset(&cmd_buff->u.s.payload, 0, sizeof(cmd_buff->u.s.payload));


        command = strtok(line_buff, " ");
        if (!command) {
                return 1; //empty lines
        }


        if (strcmp(command, "reset_time") == 0) {
                frame_type = RESET_TIME;
                cmd_buff->u.s.payload[cmd_buff->u.s.len++] = frame_type;
                gettimeofday(&new_time_ref, NULL); // update time reference

        } else if (strcmp(command, "start") == 0) {
                frame_type = OPEN_NODE_START;
                cmd_buff->u.s.payload[cmd_buff->u.s.len++] = frame_type;

                // DC BATT
                arg = strtok(NULL, " ");
                got_error |= get_val(arg, alim_d, &val);
                cmd_buff->u.s.payload[cmd_buff->u.s.len++] = val;

        } else if (strcmp(command, "stop") == 0) {
                frame_type = OPEN_NODE_STOP;
                cmd_buff->u.s.payload[cmd_buff->u.s.len++] = frame_type;

                // DC BATT
                arg = strtok(NULL, " ");
                got_error |= get_val(arg, alim_d, &val);
                cmd_buff->u.s.payload[cmd_buff->u.s.len++] = val;

        } else if (strcmp(command, "config_consumption_measure") == 0) {
                frame_type = CONFIG_POWER_POLL;
                cmd_buff->u.s.payload[cmd_buff->u.s.len++] = frame_type;

                // start stop
                arg = strtok(NULL, " ");
                if (strcmp(arg, "stop") == 0) {
                        // measures | source
                        // empty when 'stop'
                        cmd_buff->u.s.len++;
                        // status | period | average
                        cmd_buff->u.s.payload[cmd_buff->u.s.len] |= CONSUMPTION_STOP;
                        cmd_buff->u.s.len++;
                } else if (strcmp(arg, "start") == 0) {
                        // measures | source
                        // Source
                        arg = strtok(NULL, " ");
                        got_error |= get_val(arg, power_source_d, &val);
                        cmd_buff->u.s.payload[cmd_buff->u.s.len] |= val;
                        // measures
                        // Power
                        arg = strtok(NULL, " ");
                        got_error |= strcmp(arg, "p");
                        arg = strtok(NULL, " ");
                        if (atoi(arg))
                                cmd_buff->u.s.payload[cmd_buff->u.s.len] |= MEASURE_POWER;
                        // Voltage
                        arg = strtok(NULL, " ");
                        got_error |= strcmp(arg, "v");
                        arg = strtok(NULL, " ");
                        if (atoi(arg))
                                cmd_buff->u.s.payload[cmd_buff->u.s.len] |= MEASURE_VOLTAGE;
                        // Current
                        arg = strtok(NULL, " ");
                        got_error |= strcmp(arg, "c");
                        arg = strtok(NULL, " ");
                        if (atoi(arg))
                                cmd_buff->u.s.payload[cmd_buff->u.s.len] |= MEASURE_CURRENT;

                        cmd_buff->u.s.len++;


                        // status | period | average
                        cmd_buff->u.s.payload[cmd_buff->u.s.len] |= CONSUMPTION_START;
                        // period
                        arg = strtok(NULL, " ");
                        got_error |= strcmp(arg, "-p");
                        arg = strtok(NULL, " ");
                        got_error |= get_val(arg, periods_d, &val);
                        cmd_buff->u.s.payload[cmd_buff->u.s.len] |= val;


                        // average
                        arg = strtok(NULL, " ");
                        got_error |= strcmp(arg, "-a");
                        arg = strtok(NULL, " ");
                        got_error |= get_val(arg, average_d, &val);
                        cmd_buff->u.s.payload[cmd_buff->u.s.len] |= val;

                        cmd_buff->u.s.len++;

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

int write_answer(unsigned char *data, size_t len)
{
        DEBUG_PRINT("write answer, pkt len  %zu\n", len);
        if (len != 2)
                return -1;


        // errors
        uint8_t type = data[0];
        int got_error;
        char *cmd = NULL;

        got_error = 0;
        if (type == ERROR_FRAME) {
                DEBUG_PRINT("error frame\n");
                int error_code;
                // handle error frame
                got_error |= get_key(type, alim_d, &cmd);
                error_code = (int) ((char) data[1]); // sign extend
                if (got_error)
                        return -3;
                printf("%s %d\n", cmd, error_code);
        } else if ((type & MEASURES_FRAME_MASK) == MEASURES_FRAME_MASK) {
                DEBUG_PRINT("ERROR measure frame\n");
                return -2; // Measure packet should not be here
        } else {
                DEBUG_PRINT("measure frame\n");
                char *arg;
                got_error |= get_key(data[0], answers_d, &cmd);
                got_error |= get_key(data[1], ack_d, &arg);
                // CMDs acks
                if (got_error)
                        return -3;
                printf("%s %s\n", cmd, arg);
        }


        return 0;
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
                        DEBUG_PRINT("    ");
                        for (int i=0; i < 2 + cmd_buff.u.s.len; i++) {
                                DEBUG_PRINT(" %02X", cmd_buff.u.pkt[i]);
                        }

                        ret = write(reader_state->serial_fd, cmd_buff.u.pkt, cmd_buff.u.s.len + 2);
                        DEBUG_PRINT("    write ret: %i\n", ret);
                }
        }
        return NULL;
}


