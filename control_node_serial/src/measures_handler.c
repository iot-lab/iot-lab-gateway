// timerclear
#ifndef _BSD_SOURCE
#define _BSD_SOURCE
#endif//_BSD_SOURCE
#include <stdint.h>
#include <string.h>
#include <stdio.h>


// TODO remove me when not printing measures anymore
#define __STDC_FORMAT_MACROS
#include <inttypes.h>
// TODO remove me when not printing measures anymore



#include <sys/time.h>

#include "common.h"

#include "constants.h"
#include "measures_handler.h"


struct power_vals {
        unsigned int time;
        float val[3];
};

struct radio_measure_vals {
        unsigned int time;
        char rssi;
        unsigned char lqi;
};

static struct _measure_handler_state {
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

extern void init_measures_handler()
{
        timerclear(&mh_state.time_ref);
        mh_state.power.is_valid = 0;
}

static void handle_pw_pkt(unsigned char *data, size_t len)
{
        int num_measures;
        float p = 0.0, v = 0.0, c = 0.0;

        uint64_t t_s;
        uint32_t t_us;
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

                t_s  = pw_vals.time / TIME_FACTOR;
                t_us = (1000000 * (pw_vals.time % TIME_FACTOR)) / TIME_FACTOR;

                if (mh_state.power.p)
                        p = pw_vals.val[i++];
                if (mh_state.power.v)
                        v = pw_vals.val[i++];
                if (mh_state.power.c)
                        c = pw_vals.val[i++];

                // Handle absolute time with  reference time
                fprintf(LOG, "%lu.%lu:%"PRIu64".%u: %f %f %f\n",
                                mh_state.time_ref.tv_sec, mh_state.time_ref.tv_usec, t_s, t_us, p, v, c);
        }
}

static void handle_radio_measure_pkt(unsigned char *data, size_t len)
{
        int num_measures;
        signed char rssi; // 'signed' required for embedded code
        unsigned char lqi;

        uint64_t t_s;
        uint32_t t_us;

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

                t_s  = radio_vals.time / TIME_FACTOR;
                t_us = (1000000 * (radio_vals.time % TIME_FACTOR)) / TIME_FACTOR;

                rssi = radio_vals.rssi;
                lqi  = radio_vals.lqi;

                // Handle absolute time with  reference time
                fprintf(LOG, "%lu.%lu:%"PRIu64".%u: %i %u\n",
                        mh_state.time_ref.tv_sec, mh_state.time_ref.tv_usec,
                        t_s, t_us,
                        rssi, lqi);
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

