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
        {"140",  PERIOD_140us},
        {"204",  PERIOD_204us},
        {"332",  PERIOD_332us},
        {"588",  PERIOD_588us},
        {"1100", PERIOD_1100us},
        {"2116", PERIOD_2116us},
        {"4156", PERIOD_4156us},
        {"8244", PERIOD_8244us},
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
        {"3.0",   POWER_3dBm},
        {"2.8", POWER_2_8dBm},
        {"2.3", POWER_2_3dBm},
        {"1.8", POWER_1_8dBm},
        {"1.3", POWER_1_3dBm},
        {"0.7", POWER_0_7dBm},
        {"0.0",   POWER_0dBm},
        {"-1.0",  POWER_m1dBm},
        {"-2.0",  POWER_m2dBm},
        {"-3.0",  POWER_m3dBm},
        {"-4.0",  POWER_m4dBm},
        {"-5.0",  POWER_m5dBm},
        {"-7.0",  POWER_m7dBm},
        {"-9.0",  POWER_m9dBm},
        {"-12.0", POWER_m12dBm},
        {"-17.0", POWER_m17dBm},
        {NULL, 0},
};
struct dict_entry ack_d[] = {
        {"ACK", ACK},
        {"NACK", NACK},
        {NULL, 0},
};

struct dict_entry commands_d[] = {
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

        {"green_led_on", GREEN_LED_ON},
        {"green_led_blink", GREEN_LED_BLINK},

        {"test_radio_ping_pong", TEST_RADIO_PING_PONG},
        {"test_gpio", TEST_GPIO},
        {"test_i2c", TEST_I2C},
        {NULL, 0},
};
struct dict_entry radio_state_d[] = {
        {"start", RADIO_START},
        {"stop", RADIO_STOP},
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

        } else if ((strcmp(command, "start") == 0) || \
                   (strcmp(command, "stop") == 0)) {
                got_error |= get_val(command, commands_d, &frame_type);
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
        // leds control
        } else if ((strcmp(command, "green_led_on") == 0) || \
                   (strcmp(command, "green_led_blink") == 0)) {
                got_error |= get_val(command, commands_d, &frame_type);
                cmd_buff->u.s.payload[cmd_buff->u.s.len++] = frame_type;
        /* Tests commands */
        } else if ((strcmp(command, "test_radio_ping_pong") == 0) || \
                   (strcmp(command, "test_gpio") == 0) || \
                   (strcmp(command, "test_i2c") == 0)) {
                got_error |= get_val(command, commands_d, &frame_type);
                cmd_buff->u.s.payload[cmd_buff->u.s.len++] = frame_type;

                // start stop
                arg = strtok(NULL, " ");
                got_error |= get_val(arg, radio_state_d, &val);
                cmd_buff->u.s.payload[cmd_buff->u.s.len++] = val;
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

        uint8_t type;
        int got_error;
        char *cmd = NULL;


        if (len != 2) {
                return -1;
        }

        type = data[0];

        got_error = 0;
        if (type == ERROR_FRAME) {
                /*
                 * I'm only printing the error number and not what it means
                 * It's done on purpose as I don't want to add it for the moment
                 * when the code is not stable.
                 *
                 * As errors should 'never' happen, I prefer that it gets
                 * searched in the source code to find what it means
                 *
                 * It also allows adding new temporary errors on control node
                 * without intervention on this code.
                 */
                DEBUG_PRINT("error frame\n");
                int error_code;
                // handle error frame
                got_error |= get_key(type, commands_d, &cmd);
                error_code = (int) ((char) data[1]); // sign extend
                PRINT_MSG("%s %d\n", cmd, error_code);
        } else {
                DEBUG_PRINT("Commands ACKS\n");
                char *arg;
                got_error |= get_key(type, commands_d, &cmd);
                got_error |= get_key(data[1], ack_d, &arg);
                // CMDs acks
                if (got_error) {
                        PRINT_ERROR("invalid answer: %02X %02X\n",
                                        data[0], data[1]);
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
        char *command_save  = (char *)malloc(2048);
        int ret;

        int n;
        while ((n = getline(&line_buff, &buff_size, stdin)) != -1) {
                DEBUG_PRINT("Command: %s: ", line_buff);
                line_buff[n - 1] = '\0'; // remove new line
                strncpy(command_save, line_buff, 2048);
                DEBUG_PRINT("Command: %s: ", line_buff);
                ret = parse_cmd(line_buff, &cmd_buff);
                if (ret) {
                        PRINT_ERROR("Invalid command: '%s'\n", command_save);
                } else {
                        DEBUG_PRINT("    ");
                        DEBUG_PRINT_PACKET(cmd_buff.u.pkt,
                                        2 + cmd_buff.u.s.len);
                        ret = write(reader_state->serial_fd, cmd_buff.u.pkt,
                                        cmd_buff.u.s.len + 2);
                        DEBUG_PRINT("    write ret: %i\n", ret);
                }
        }
        exit(0);
        return NULL;
}
