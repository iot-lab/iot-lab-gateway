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

#include <stdio.h>
#include <oml2/omlc.h>
#define OML_FROM_MAIN
#include "control_node_measures_oml.h"

#include "oml_measures.h"
#include "common.h"

static int oml_measure_started = 0;
static int oml_print = 0;

int oml_measures_start(char *oml_config_file_path, int print_measures)
{
    /*
     * Do print measures
     */
    oml_print = print_measures;

    /*
     * Do write oml files
     */
    if (NULL == oml_config_file_path)
        return 0;

    int result;
    const char *argv[] = {
        "argv0",
        "--oml-log-level", "-2",  // log only errors
        "--oml-log-file", "/tmp/oml.log",
        "--oml-config", oml_config_file_path
    };
    int argc = (sizeof(argv) / sizeof(char *));

    result = omlc_init("control_node_measures", &argc, argv, NULL);
    if (result == -1) {
        PRINT_ERROR("omlc_init failed: %d\n", result);
        return result;
    }

    oml_register_mps();

    result = omlc_start();
    if (result == -1) {
        PRINT_ERROR("omlc_start failed: %d\n", result);
        return result;
    }

    oml_measure_started = 1;
    return 0;
}

int oml_measures_stop(void)
{
    int ret = 0;
    if (oml_measure_started)
        ret = omlc_close();

    oml_measure_started = 0;
    oml_print = 0;
    return ret;
}


void oml_measures_consumption(uint32_t timestamp_s, uint32_t timestamp_us,
        double power, double voltage, double current)
{
    if (oml_measure_started)
        oml_inject_consumption(g_oml_mps_control_node_measures->consumption,
                timestamp_s, timestamp_us, power, voltage, current);
    if (oml_print)
        PRINT_MEASURE("consumption_measure %u.%06u %f %f %f\n",
                timestamp_s, timestamp_us, power, voltage, current);
}

void oml_measures_radio(uint32_t timestamp_s, uint32_t timestamp_us,
        uint32_t channel, int32_t rssi)
{
    if (oml_measure_started)
        oml_inject_radio(g_oml_mps_control_node_measures->radio,
                timestamp_s, timestamp_us, channel, rssi);
    if (oml_print)
        PRINT_MEASURE("radio_measure %u.%06u %u %i\n",
                timestamp_s, timestamp_us, channel, rssi);
}

void oml_measures_sniffer(uint32_t timestamp_s, uint32_t timestamp_us,
        uint32_t channel, int32_t rssi, uint32_t lqi,
        uint8_t crc_ok, uint32_t length)
{
    if (oml_measure_started)
        oml_inject_sniffer(g_oml_mps_control_node_measures->sniffer,
                timestamp_s, timestamp_us,
                channel, rssi, lqi, crc_ok, length);
    if (oml_print)
        PRINT_MEASURE("sniffer %u.%06u %u %i %u %s %u\n",
                timestamp_s, timestamp_us,
                channel, rssi, lqi, (crc_ok ? "crc_ok" : "crc_error"), length);
}

void oml_measures_event(uint32_t timestamp_s, uint32_t timestamp_us,
        uint32_t value, const char* name)
{
    if (oml_measure_started)
        oml_inject_event(g_oml_mps_control_node_measures->event,
                timestamp_s, timestamp_us,
                value, name);
    if (oml_print)
        PRINT_MEASURE("event %u.%06u %u %s\n",
                timestamp_s, timestamp_us,
                value, name);
}
