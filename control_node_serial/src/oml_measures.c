#include <stdio.h>
#include <oml2/omlc.h>
#define OML_FROM_MAIN
#include "control_node_measures_oml.h"

#include "oml_measures.h"
#include "common.h"

static int oml_measure_started = 0;

int oml_measures_start(char *oml_config_file_path)
{
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


void oml_measures_consumption(uint32_t timestamp_s, uint32_t timestamp_us,
                              double power, double voltage, double current)
{
        if (!oml_measure_started)
            return;
        oml_inject_consumption(g_oml_mps_control_node_measures->consumption,
                               timestamp_s, timestamp_us,
                               power, voltage, current);
}

void oml_measures_radio(uint32_t timestamp_s, uint32_t timestamp_us,
                        uint32_t channel, int32_t rssi)
{
        if (!oml_measure_started)
            return;
        oml_inject_radio(g_oml_mps_control_node_measures->radio,
                         timestamp_s, timestamp_us,
                         channel, rssi);
}

void oml_measures_sniffer(uint32_t timestamp_s, uint32_t timestamp_us,
                          uint32_t channel, uint8_t crc_ok,
                          int32_t rssi, uint32_t lqi, uint32_t length)
{
        if (!oml_measure_started)
            return;
        oml_inject_sniffer(g_oml_mps_control_node_measures->sniffer,
                        timestamp_s, timestamp_us,
                        channel, crc_ok, rssi, lqi, length);
}

void oml_measures_event(uint32_t timestamp_s, uint32_t timestamp_us,
                        uint32_t value, const char* name)
{
        if (!oml_measure_started)
            return;
        oml_inject_event(g_oml_mps_control_node_measures->event,
                        timestamp_s, timestamp_us,
                        value, name);
}

int oml_measures_stop(void)
{
        if (!oml_measure_started)
                return 0;
        oml_measure_started = 0;
        return omlc_close();
}
