#ifndef _BSD_SOURCE
#define _BSD_SOURCE
#endif // _BSD_SOURCE
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
#include "utils.h"


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

struct dict_entry alim_d[] = {
        {"dc", DC},
        {"battery", BATTERY},
        {NULL, 0},
};


/* Consumption dicts */
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


/* Radio dicts */
struct dict_entry radio_power_d[] = {
        {"3dBm",   POWER_3dBm},
        {"2.8dBm", POWER_2_8dBm},
        {"2.3dBm", POWER_2_3dBm},
        {"1.8dBm", POWER_1_8dBm},
        {"1.3dBm", POWER_1_3dBm},
        {"0.7dBm", POWER_0_7dBm},
        {"0dBm",   POWER_0dBm},
        {"-1dBm",  POWER_m1dBm},
        {"-2dBm",  POWER_m2dBm},
        {"-3dBm",  POWER_m3dBm},
        {"-4dBm",  POWER_m4dBm},
        {"-5dBm",  POWER_m5dBm},
        {"-7dBm",  POWER_m7dBm},
        {"-9dBm",  POWER_m9dBm},
        {"-12dBm", POWER_m12dBm},
        {"-17dBm", POWER_m17dBm},
        {NULL, 0},
};


/* dict used for answers, to translate code to string */

struct dict_entry answers_d[] = {
        {"error", ERROR_FRAME},
        {"start", OPEN_NODE_START},
        {"stop", OPEN_NODE_STOP},
        {"reset_time", RESET_TIME},

        {"config_radio_signal", CONFIG_RADIO},
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
        pthread_t reader_thread;
} reader_state;


int command_reader_start(int serial_fd)
{
        int ret;

        reader_state.serial_fd = serial_fd;
        ret = pthread_create(&reader_state.reader_thread, NULL, read_commands,
                        &reader_state);
        return ret;
}


static int parse_cmd(char *line_buff, struct command_buffer *cmd_buff)
{
        char *command = NULL;
        char *arg = NULL;

        uint8_t frame_type = 0;
        uint8_t val        = 0;
        int got_error      = 0;


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
                        if (atoi(arg)) // != 0 (== 1 actually)
                                cmd_buff->u.s.payload[cmd_buff->u.s.len] |= MEASURE_POWER;
                        // Voltage
                        arg = strtok(NULL, " ");
                        got_error |= strcmp(arg, "v");
                        arg = strtok(NULL, " ");
                        if (atoi(arg)) // != 0 (== 1 actually)
                                cmd_buff->u.s.payload[cmd_buff->u.s.len] |= MEASURE_VOLTAGE;
                        // Current
                        arg = strtok(NULL, " ");
                        got_error |= strcmp(arg, "c");
                        arg = strtok(NULL, " ");
                        if (atoi(arg)) // != 0 (== 1 actually)
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
        } else if (strcmp(command, "config_radio_signal") == 0) {
                frame_type = CONFIG_RADIO;
                cmd_buff->u.s.payload[cmd_buff->u.s.len++] = frame_type;

                // radio power
                arg = strtok(NULL, " ");
                got_error |= get_val(arg, radio_power_d, &val);
                cmd_buff->u.s.payload[cmd_buff->u.s.len++] = val;

                // radio channel
                arg = strtok(NULL, " ");
                val = (uint8_t) atoi(arg);
                // channel in [[11, 26]]
                if (val < 11 || val > 26)
                        got_error |=1;
                cmd_buff->u.s.payload[cmd_buff->u.s.len++] = val;

        } else if (strcmp(command, "config_radio_measure") == 0) {
                frame_type = CONFIG_RADIO_POLL;
                cmd_buff->u.s.payload[cmd_buff->u.s.len++] = frame_type;

                // start stop
                arg = strtok(NULL, " ");
                if (strcmp(arg, "stop") == 0) {
                        cmd_buff->u.s.payload[cmd_buff->u.s.len++] = RADIO_STOP;
                        cmd_buff->u.s.payload[cmd_buff->u.s.len++] = 0; // empty
                        cmd_buff->u.s.payload[cmd_buff->u.s.len++] = 0; // empty
                } else if (strcmp(arg, "start") == 0) {
                        uint32_t freq;
                        cmd_buff->u.s.payload[cmd_buff->u.s.len++] = RADIO_START;

                        // measure freq
                        arg = strtok(NULL, " ");
                        freq = (uint32_t) atoi(arg);
                        if (freq < 2 || freq > 499)
                                got_error |=1;
                        cmd_buff->u.s.payload[cmd_buff->u.s.len++] = (\
                                        freq & 0xFF);  // LSB
                        cmd_buff->u.s.payload[cmd_buff->u.s.len++] = (\
                                        (freq >> 8) & 0xFF);  // MSB

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

        uint8_t type = data[0];
        int got_error;
        char *cmd = NULL;

        got_error = 0;
        if (type == ERROR_FRAME) {
                DEBUG_PRINT("error frame\n");
                int error_code;
                // handle error frame
                got_error |= get_key(type, answers_d, &cmd);
                error_code = (int) ((char) data[1]); // sign extend
                PRINT_MSG("%s %d\n", cmd, error_code);
        } else if ((type & MEASURES_FRAME_MASK) == MEASURES_FRAME_MASK) {
                DEBUG_PRINT("ERROR measure frame\n");
                return -2; // Measure packet should not be here
        } else {
                DEBUG_PRINT("Commands ACKS\n");
                char *arg;
                got_error |= get_key(type, answers_d, &cmd);
                got_error |= get_key(data[1], ack_d, &arg);
                // CMDs acks
                if (got_error) {
                        return -3;
                }
                PRINT_MSG("%s %s\n", cmd, arg);
        }


        return 0;
}


static void *read_commands(void *attr)
{
        struct state *reader_state = (struct state *) attr;

        struct command_buffer cmd_buff;
        size_t buff_size = 2048;
        char *line_buff  = (char *)malloc(buff_size);
        int ret;

        int n;
        while ((n = getline(&line_buff, &buff_size, stdin)) != -1) {
                DEBUG_PRINT("Command: %s: ", line_buff);
                line_buff[n - 1] = '\0'; // remove new line
                DEBUG_PRINT("Command: %s: ", line_buff);
                ret = parse_cmd(line_buff, &cmd_buff);
                if (ret) {
                        DEBUG_PRINT("Error parsing\n");
                } else {
                        DEBUG_PRINT("    ");
                        DEBUG_PRINT_PACKET(cmd_buff.u.pkt, 2 + cmd_buff.u.s.len);
                        ret = write(reader_state->serial_fd, cmd_buff.u.pkt, cmd_buff.u.s.len + 2);
                        DEBUG_PRINT("    write ret: %i\n", ret);
                }
        }
        exit(0);
        return NULL;
}


