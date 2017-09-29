/*******************************************************************************
# This file is a part of IoT-LAB gateway_code
# Copyright (C) 2015 INRIA (Contact: admin@iot-lab.info)
# Contributor(s) : see AUTHORS file
#
# This software is governed by the CeCILL license under French law
# and abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# http://www.cecill.info.
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.
*******************************************************************************/

#include <stdint.h>
#include <string.h>
#include <stdio.h>

#include <sys/time.h>
#include <arpa/inet.h>
#include <math.h>
#include <assert.h>

#include "time_ref.h"
#include "common.h"
#include "constants.h"
#include "oml_measures.h"
#include "measures_handler.h"
#include "sniffer_server.h"


struct consumption_measure {
    float val[3];
};

struct radio_measure {
    uint8_t channel;
    int8_t rssi;
};

static struct _measure_handler_state {
    struct {
        int p;
        int v;
        int c;
        int power_source;
        size_t meas_len;
    } consumption;
} mh_state;


static void calculate_time_extended(struct timeval *total_time,
        uint32_t pkt_timeref_s, uint32_t time_us)
{
    total_time->tv_sec  = pkt_timeref_s;
    total_time->tv_usec = time_us;

    // correct if tv_usec is > 1second
    total_time->tv_sec += (total_time->tv_usec / 1000000);
    total_time->tv_usec %= 1000000;
}

static void extract_data(uint8_t *dst, uint8_t **src, size_t len);

void measures_handler_start(int print_measures, char *oml_config_file_path)
{
    oml_measures_start(oml_config_file_path, print_measures);
}

void measures_handler_stop()
{
    oml_measures_stop();
}


typedef void (*meas_handler_t)(uint8_t *buf, struct timeval *time);


static void handle_oml_measure(uint8_t *data, size_t len, uint8_t *meas_buf,
        size_t meas_size, meas_handler_t handler, char *measure_str)
{
    struct timeval timestamp;
    size_t rlen;

    uint32_t t_ref_s;
    uint32_t t_us;
    uint8_t num_meas  = data[1];
    uint8_t *data_ptr = &data[2];

    // length == (header + time_ref_seconds) + n_measures * (t_us + len)
    rlen  = 2 + sizeof(uint32_t); // header
    rlen += num_meas * (sizeof(uint32_t) + meas_size); // measures
    if (len != rlen) {
        PRINT_ERROR("Invalid %s pkt len: %zu != expected %zu\n",
                measure_str, len, rlen);
        return;
    }

    /*
     * Handle payload
     */
    // copy basetime for seconds
    extract_data((uint8_t *)&t_ref_s, &data_ptr, sizeof(uint32_t));

    for (int i = 0; i < num_meas; i++) {
        // Time
        extract_data((uint8_t *)&t_us, &data_ptr, sizeof(uint32_t));
        calculate_time_extended(&timestamp, t_ref_s, t_us);

        // Measure
        extract_data(meas_buf, &data_ptr, meas_size);
        handler(meas_buf, &timestamp);
    }
}

static void radio_handler(uint8_t *buf, struct timeval *time)
{
    struct radio_measure radio;
    memcpy(&radio, buf, sizeof(radio));
    oml_measures_radio(time->tv_sec, time->tv_usec,
            radio.channel, radio.rssi);
}


/*
 * RFC 5905                   NTPv4 Specification                 June 2010
 */
/* 1970 - 1900 in seconds */
#define JAN_1970        2208988800UL
/* 2^32 as an int */
#define FRAC       (((uint64_t)1) << 32)

enum zep_format_t {
    zep_idx_preamble             = 0,
    zep_idx_version              = 2,
    zep_idx_type                 = 3,

    zep_idx_channel              = 4,
    zep_idx_device_id            = 5,
    zep_idx_lqi                  = 8,
    zep_idx_ntp_time_msb         = 9,
    zep_idx_ntp_time_lsb         = 13,
    zep_idx_seqno                = 17,

    zep_idx_reserved             = 21,
    zep_idx_reserved_rx_time_len = 21,
    zep_idx_reserved_rssi        = 23,
    zep_idx_len                  = 31,
};

static void handle_radio_sniffer(uint8_t *data, size_t len)
{
    size_t rlen;
    struct timeval timestamp;
    uint32_t timestamp_ntp_msb;
    uint32_t timestamp_ntp_lsb;
    uint8_t channel;
    int8_t rssi;
    uint8_t lqi;
    uint8_t pkt_len;

    uint8_t *data_ptr = &data[1];
    rlen = 1;  //header

    // Could read captured_length
    rlen += (zep_idx_len + 1);
    if (len < rlen) {
        PRINT_ERROR("Invalid sniff pkt len: %zu < %zu(len)\n", len, rlen);
        return;
    }

    pkt_len = data_ptr[zep_idx_len];
    // big enough to get 'payload' value
    rlen += pkt_len;
    if (len != rlen) {
        PRINT_ERROR("Invalid sniff pkt len: %zu != %zu(payload)\n", len, rlen);
        return;
    }

    sniffer_server_send_packet(data_ptr, len);

    // Extract data to put in oml traces
    channel = data_ptr[zep_idx_channel];
    lqi = data_ptr[zep_idx_lqi];
    rssi = data_ptr[zep_idx_reserved_rssi];
    memcpy(&timestamp_ntp_msb, &data_ptr[zep_idx_ntp_time_msb], sizeof(uint32_t));
    memcpy(&timestamp_ntp_lsb, &data_ptr[zep_idx_ntp_time_lsb], sizeof(uint32_t));

    timestamp.tv_sec = (uint32_t) (ntohl(timestamp_ntp_msb) - JAN_1970);
    timestamp.tv_usec = (uint32_t) (((uint64_t)ntohl(timestamp_ntp_lsb) * 1000000) / FRAC);

    oml_measures_sniffer(timestamp.tv_sec, timestamp.tv_usec,
            channel, rssi, lqi, 1,  // crc_ok
            pkt_len - 2);  // Added two bytes for ZEP maybe remove later
}

static void consumption_handler(uint8_t *buf, struct timeval *time)
{
    struct consumption_measure cons;
    memcpy(&cons, buf, sizeof(cons));

    size_t i = 0;

    /* Load values that exist */
    float p = (mh_state.consumption.p ? cons.val[i++] : NAN);
    float v = (mh_state.consumption.v ? cons.val[i++] : NAN);
    float c = (mh_state.consumption.c ? cons.val[i++] : NAN);

    oml_measures_consumption(time->tv_sec, time->tv_usec, p, v, c);
}

static void config_consumption(int power_source, int p, int v, int c)
{
    // cleanup for new configuration
    memset(&mh_state.consumption, 0, sizeof(mh_state.consumption));

    mh_state.consumption.power_source = power_source;

    mh_state.consumption.meas_len = 0;
    if (p) {
        mh_state.consumption.p = 1;
        mh_state.consumption.meas_len += sizeof(float);
    }
    if (v) {
        mh_state.consumption.v = 1;
        mh_state.consumption.meas_len += sizeof(float);
    }
    if (c) {
        mh_state.consumption.c = 1;
        mh_state.consumption.meas_len += sizeof(float);
    }
}

static void handle_ack_pkt(uint8_t *data, size_t len)
{
    // ACK_FRAME | config_type | [config]
    (void)len;
    uint8_t ack_type = data[1];
    uint8_t config   = data[2];
    struct timeval time_ack, time_diff;


    switch (ack_type) {
        case SET_TIME:
            gettimeofday(&time_ack, NULL);
            timeval_substract(&time_diff, &time_ack, &set_time_ref);
            PRINT_MSG("config_ack set_time %lu.%06lu\n",
                    time_diff.tv_sec, time_diff.tv_usec);
            timerclear(&set_time_ref);
            break;
        case CONFIG_CONSUMPTION:
            PRINT_MSG("config_ack config_consumption_measure\n");
            config_consumption(
                    config & (PW_SRC_3_3V | PW_SRC_5V | PW_SRC_BATT),
                    config & MEASURE_POWER,
                    config & MEASURE_VOLTAGE,
                    config & MEASURE_CURRENT);
            break;
        case CONFIG_RADIO_STOP:
            PRINT_MSG("config_ack config_radio_stop\n");
            break;
        case CONFIG_RADIO_MEAS:
            PRINT_MSG("config_ack config_radio_measure\n");
            break;
        default:
            PRINT_ERROR("Unkown ACK frame 0x%02x\n", ack_type);
            break;
    }
}

int handle_measure_pkt(uint8_t *data, size_t len)
{
    uint8_t pkt_type = data[0];
    meas_handler_t handler;

    size_t meas_size;
    char  *meas_str;
    union {
        struct radio_measure radio;
        struct consumption_measure consumption;
        uint8_t data;
    } buf;

    switch (pkt_type) {
        // Packet with only one value different format
        case ACK_FRAME:
            handle_ack_pkt(data, len);
            return 0;
        case RADIO_SNIFFER_FRAME:
            handle_radio_sniffer(data, len);
            return 0;

            // Packet with multiple values
        case CONSUMPTION_FRAME:
            handler  = consumption_handler;
            meas_str = "consumption";
            meas_size = mh_state.consumption.meas_len;
            break;
        case RADIO_MEAS_FRAME:
            handler   = radio_handler;
            meas_str  = "radio";
            meas_size = sizeof(struct radio_measure);
            break;

        default:
            return -1;
    }
    handle_oml_measure(data, len, (uint8_t *)&buf, meas_size, handler,
            meas_str);
    return 0;
}

static void extract_data(uint8_t *dst, uint8_t **src, size_t len)
{
    memcpy(dst, *src, len);
    *src += len;
}
