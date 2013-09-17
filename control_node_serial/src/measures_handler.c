// timerclear
#ifndef _BSD_SOURCE
#define _BSD_SOURCE
#endif//_BSD_SOURCE
#include <stdint.h>
#include <string.h>
#include <stdio.h>

#include <sys/time.h>
#include <math.h>

#include "common.h"
#include "constants.h"
#include "oml_measures.h"
#include "measures_handler.h"


struct power_vals {
        unsigned int time;
        float val[3];
};

struct radio_measure_vals {
        unsigned int time;
        signed char rssi;
        unsigned char lqi;
};

static struct _measure_handler_state {
        int print_measures;
        struct timeval time_ref;
        struct {
                int is_valid;
                int p;
                int v;
                int c;
                int power_source;
                size_t raw_values_len;
        } power;
} mh_state;

static void calculate_time(struct timeval *total_time, const struct timeval *time_ref,
                           unsigned int cn_time)
{
        total_time->tv_sec  = time_ref->tv_sec;
        total_time->tv_usec = time_ref->tv_usec;

        total_time->tv_sec  += cn_time / TIME_FACTOR;
        total_time->tv_usec += (suseconds_t) (
                        (1000000 * ((uint64_t) cn_time % TIME_FACTOR))
                        / TIME_FACTOR);

        if (1000000 <= total_time->tv_usec) {
                total_time->tv_usec -= 1000000;
                total_time->tv_sec  += 1;
        }
}


void measures_handler_start(int print_measures, char *oml_config_file_path)
{
        timerclear(&mh_state.time_ref);
        mh_state.power.is_valid = 0;
        mh_state.print_measures = print_measures;
        if (NULL != oml_config_file_path) {
                /* only start oml when a config file is given
                 * calls to oml_inject_* will be ignored
                 * and oml_measures_close will return -1 but ignored
                 */
                oml_measures_start(oml_config_file_path);
        }
}

void measures_handler_stop()
{
        oml_measures_stop();
}

static void handle_pw_pkt(unsigned char *data, size_t len)
{
        int num_measures;
        float p = NAN, v = NAN, c = NAN;

        struct timeval timestamp;
        unsigned char *current_data_ptr;
        struct power_vals pw_vals;

        size_t values_len;

        if (!mh_state.power.is_valid) {
                // Should have got a 'CONFIG_POWER_POLL' ACK before
                PRINT_ERROR("Got PW measure without being configured\n%s", "");
                return;
        }

        values_len       = mh_state.power.raw_values_len;
        num_measures     = data[1];
        current_data_ptr = &data[2];

        size_t expected_len = 2 + values_len * num_measures;

        if (expected_len != len) {
                PRINT_ERROR("Invalid measure pkt len: %zu != expected %zu\n",
                                len, expected_len);
                return;
        }

        for (int j = 0; j < num_measures; j++) {
                int i = 0;

                memcpy(&pw_vals, current_data_ptr, values_len);
                current_data_ptr += values_len;
                calculate_time(&timestamp, &mh_state.time_ref, pw_vals.time);

                if (mh_state.power.p)
                        p = pw_vals.val[i++];
                if (mh_state.power.v)
                        v = pw_vals.val[i++];
                if (mh_state.power.c)
                        c = pw_vals.val[i++];

                oml_measures_consumption(timestamp.tv_sec, timestamp.tv_usec,
                                         p, v, c);
                PRINT_MEASURE(mh_state.print_measures,
                              "%s %lu.%06lu %f %f %f\n", "consumption_measure",
                              timestamp.tv_sec, timestamp.tv_usec,
                              p, v, c);
        }
}

static void handle_radio_measure_pkt(unsigned char *data, size_t len)
{
        int num_measures;

        struct timeval timestamp;

        unsigned char *current_data_ptr;
        struct radio_measure_vals radio_vals;

        size_t values_len = 6;

        num_measures     = data[1];
        current_data_ptr = &data[2];

        size_t expected_len = 2 + values_len * num_measures;
        if (expected_len != len) {
                PRINT_ERROR("Invalid measure pkt len: %zu != expected %zu\n",
                                len, expected_len);
                return;
        }

        for (int j = 0; j < num_measures; j++) {
                memcpy(&radio_vals, current_data_ptr, values_len);
                current_data_ptr += values_len;

                calculate_time(&timestamp, &mh_state.time_ref, radio_vals.time);

                oml_measures_radio(timestamp.tv_sec, timestamp.tv_usec,
                                   radio_vals.rssi, radio_vals.lqi);

                PRINT_MEASURE(mh_state.print_measures, "%s %lu.%06lu %i %u\n",
                              "radio_measure",
                              timestamp.tv_sec, timestamp.tv_usec,
                              radio_vals.rssi, radio_vals.lqi);
        }
}

static void handle_ack_pkt(unsigned char *data, size_t len)
{
        // ACK_FRAME | config_type | [config]
        // if (len != 3) {
        //         PRINT_ERROR("Invalid len for ACK %zu\n", len);
        //         return;
        // }
        (void) len;
        uint8_t ack_type = data[1];
        uint8_t config   = data[2];


        switch (ack_type) {
                case RESET_TIME:
                        PRINT_MSG("config_ack reset_time\n");
                        gettimeofday(&mh_state.time_ref, NULL); // update time reference
                        break;
                case CONFIG_POWER_POLL:
                        PRINT_MSG("config_ack config_consumption_measure\n");
                        // cleanup for new configuration
                        memset(&mh_state.power, 0, sizeof(mh_state.power));

                        mh_state.power.is_valid = 1;
                        mh_state.power.power_source = config &
                                (SOURCE_3_3V | SOURCE_5V | SOURCE_BATT);

                        mh_state.power.raw_values_len = sizeof(unsigned int);
                        if (config & MEASURE_POWER) {
                                mh_state.power.p = 1;
                                mh_state.power.raw_values_len += sizeof(float);
                        }
                        if (config & MEASURE_VOLTAGE) {
                                mh_state.power.v = 1;
                                mh_state.power.raw_values_len += sizeof(float);
                        }
                        if (config & MEASURE_CURRENT) {
                                mh_state.power.c = 1;
                                mh_state.power.raw_values_len += sizeof(float);
                        }
                        break;
                case CONFIG_RADIO:
                        PRINT_MSG("config_ack config_radio_signal\n");
                        break;
                case CONFIG_RADIO_POLL:
                        PRINT_MSG("config_ack config_radio_measure\n");
                        break;
                default:
                        PRINT_ERROR("Unkown ACK frame 0x%02x\n", ack_type);
                        break;
        }
}

int handle_measure_pkt(unsigned char *data, size_t len)
{

        uint8_t pkt_type = data[0];

        switch (pkt_type) {
                case PW_POLL_FRAME:
                        handle_pw_pkt(data, len);
                        break;
                case RADIO_POLL_FRAME:
                        handle_radio_measure_pkt(data, len);
                        break;
                case ACK_FRAME:
                        handle_ack_pkt(data, len);
                        break;
                default:
                        return -1;
                        break;
        }
        return 0;
}
