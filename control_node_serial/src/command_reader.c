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

#include "time_ref.h"
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
        {"3.3V",  PW_SRC_3_3V},
        {"5V",    PW_SRC_5V},
        {"BATT",  PW_SRC_BATT},
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
        {"error",      ERROR_FRAME},

        {"start",      OPEN_NODE_START},
        {"stop",       OPEN_NODE_STOP},
        {"set_time",   SET_TIME},

        {"green_led_on",    GREEN_LED_ON},
        {"green_led_blink", GREEN_LED_BLINK},


        {"config_radio_stop",    CONFIG_RADIO_STOP},
        {"config_radio_measure", CONFIG_RADIO_MEAS},
        //{"config_radio_noise",   CONFIG_RADIO_NOISE},
        //{"config_radio_sniffer", CONFIG_SNIFFER},

        //{"config_fake_sensor", CONFIG_SENSOR},

        {"config_consumption_measure", CONFIG_CONSUMPTION},


        {"test_radio_ping_pong", TEST_RADIO_PING_PONG},
        {"test_gpio",    TEST_GPIO},
        {"test_i2c",     TEST_I2C2},
        {"test_pps",     TEST_PPS},
        {"test_got_pps", TEST_GOT_PPS},
        {NULL, 0},
};

struct dict_entry state_d[] = {
        {"start", START},
        {"stop",  STOP},
        {NULL, 0},
};

static void *read_commands(void *attr);
static void append_data(struct command_buffer *cmd_buff, void *data,
                size_t size);
static uint32_t parse_channels_list(char *channels_list);


struct state {
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

        char *arguments = NULL;

        uint8_t frame_type = 0;
        uint8_t val        = 0;
        uint8_t aux        = 0;
        int got_error      = 0;


        cmd_buff->u.s.sync = SYNC_BYTE;
        cmd_buff->u.s.len  = 0;
        memset(&cmd_buff->u.s.payload, 0, sizeof(cmd_buff->u.s.payload));


        command = strtok_r(line_buff, " ", &arguments);
        if (!command)
                return 1;  //empty lines
        /* Put command */
        got_error |= get_val(command, commands_d, &frame_type);
        append_data(cmd_buff, &frame_type, sizeof(uint8_t));


        /*
         * add command arguments
         */
        if (strcmp(command, "set_time") == 0) {
                gettimeofday(&set_time_ref, NULL);
                append_data(cmd_buff, &set_time_ref.tv_sec,  sizeof(uint32_t));
                append_data(cmd_buff, &set_time_ref.tv_usec, sizeof(uint32_t));

        } else if ((strcmp(command, "start") == 0) || \
                   (strcmp(command, "stop") == 0)) {
                /*
                 * 1B: DC/BATTERY
                 */
                // only one argument 'dc' or 'battery
                arg = strtok_r(NULL, " ", &arguments);
                got_error |= get_val(arg, alim_d, &val);
                append_data(cmd_buff, &val, sizeof(uint8_t));

        } else if (strcmp(command, "config_consumption_measure") == 0) {
                /*
                 * 1B: start/stop
                 * 1B: source | measures
                 * 1B: period | average
                 */
                char start_stop[8];
                char pw_src[8];
                int p, v, c;
                char period[8], average[8];
                uint8_t state = 0;

                int count = sscanf(arguments,
                        "%8s"
                        "%8s p %i v %i c %i -p %8s -a %8s",  // for start
                        start_stop,
                        pw_src, &p, &v, &c, period, average);

                if (count < 1)
                        return 1;

                /* start/stop */
                got_error |= get_val(start_stop, state_d, &state);
                append_data(cmd_buff, &state, sizeof(uint8_t));

                switch ((enum mode)state) {
                case STOP:
                        // config has all zero
                        aux = 0;
                        append_data(cmd_buff, &aux, sizeof(uint8_t));
                        append_data(cmd_buff, &aux, sizeof(uint8_t));
                        break;
                case START:
                        if (count != 7)
                            return 1;

                        // source | measures
                        got_error |= get_val(pw_src, power_source_d, &val);
                        aux  = val;
                        aux |= (!!p * MEASURE_POWER);
                        aux |= (!!v * MEASURE_VOLTAGE);
                        aux |= (!!c * MEASURE_CURRENT);
                        append_data(cmd_buff, &aux, sizeof(uint8_t));

                        // period | average
                        aux = 0;
                        got_error |= get_val(period, periods_d, &val);
                        aux |= val;
                        got_error |= get_val(average, average_d, &val);
                        aux |= val;
                        append_data(cmd_buff, &aux, sizeof(uint8_t));
                        break;
                default:
                        got_error = 1;
                        break;
                }
        } else if (strcmp(command, "config_radio_stop") == 0) {
                ;

        } else if (strcmp(command, "config_radio_measure") == 0) {
                char channels_list[256] = {'\0'};
                unsigned int period, num_per_channel;

                int count = sscanf(arguments, "%256s %i %i",
                        channels_list, &period, &num_per_channel);

                if (3 != count)
                        return 1;
                if ((period & 0xFFFF) == 0)  // non zero and hold on 16bit
                        return 2;
                uint32_t channels_flag = parse_channels_list(channels_list);
                if (0 == channels_flag)
                        return 3;  // no channel given

                append_data(cmd_buff, &channels_flag, sizeof(uint32_t));
                append_data(cmd_buff, &period, sizeof(uint16_t));
                append_data(cmd_buff, &num_per_channel, sizeof(uint8_t));

        } else if (strcmp(command, "test_radio_ping_pong") == 0) {

                uint8_t state;
                char start_stop[8];
                char tx_power[8];
                unsigned int channel;

                int count = sscanf(arguments,
                        "%8s"
                        "%i %8s",  // for start
                        start_stop,
                        &channel, tx_power);

                /* start/stop */
                if (count < 1)
                        return 1;
                got_error |= get_val(start_stop, state_d, &state);
                append_data(cmd_buff, &state, sizeof(uint8_t));

                switch ((enum mode) state) {
                case STOP:
                        aux = 0;  // config has all zero
                        append_data(cmd_buff, &aux, sizeof(uint8_t));
                        append_data(cmd_buff, &aux, sizeof(uint8_t));
                        break;
                case START:
                        if (count != 3)
                                return 1;
                        got_error |= get_val(tx_power, radio_power_d, &val);
                        if (channel < 11 || channel > 26)
                                got_error = 1;

                        append_data(cmd_buff, &channel, sizeof(uint8_t));
                        append_data(cmd_buff, &val, sizeof(uint8_t));
                        break;
                default:
                        got_error = 1;
                        break;
                }

        // leds control and no args commands
        } else if ((strcmp(command, "green_led_on") == 0) || \
                   (strcmp(command, "green_led_blink") == 0) || \
                   (strcmp(command, "test_got_pps") == 0)) {
                ;
        /* Tests commands (start stop)*/
        } else if ((strcmp(command, "test_gpio") == 0) || \
                   (strcmp(command, "test_i2c") == 0) || \
                   (strcmp(command, "test_pps") == 0)) {
                // start stop
                arg = strtok_r(NULL, " ", &arguments);
                got_error |= get_val(arg, state_d, &val);
                cmd_buff->u.s.payload[cmd_buff->u.s.len++] = val;
        }  // error case allready handled

        return got_error;
}


static void append_data(struct command_buffer *cmd_buff, void *data,
                size_t size)
{
        memcpy(&cmd_buff->u.s.payload[cmd_buff->u.s.len], data, size);
        cmd_buff->u.s.len += size;
}

static uint32_t parse_channels_list(char *channels_list)
{
        uint32_t channels_flag = 0;
        char *chan;
        int channel;

        chan = strtok(channels_list, ",");
        while (chan != NULL) {
                // channel 11 in bit num 11
                // channel 26 in bit num 26
                channel = atoi(chan);
                if (channel >= 11 && channel <= 26)
                    channels_flag |= 1 << channel;

                chan = strtok(NULL, ",");
        }
        return channels_flag;
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
        PRINT_MSG("cn_serial_ready\n");
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
