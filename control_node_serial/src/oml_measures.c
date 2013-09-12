#include <stdio.h>
#include <oml2/omlc.h>

#include "oml_measures.h"
#include "common.h"

OmlMPDef measure_point_consumption [] = {
        { "timestamp_s",  OML_UINT64_VALUE},
        { "timestamp_us", OML_UINT32_VALUE},
        { "current",      OML_DOUBLE_VALUE},
        { "voltage",      OML_DOUBLE_VALUE},
        { "power",        OML_DOUBLE_VALUE},
        { NULL, (OmlValueT)0 }
};


OmlMPDef measure_point_radio [] = {
        { "timestamp_s",  OML_UINT64_VALUE},
        { "timestamp_us", OML_UINT32_VALUE},
        { "rssi",         OML_INT32_VALUE},
        { "lqi",          OML_INT32_VALUE},
        { NULL, (OmlValueT)0 }
};

static OmlMP *mp_consumption = NULL;
static OmlMP *mp_radio = NULL;


int oml_measures_init(char *oml_config_file_path)
{
        //const char *argv[256] = {NULL};
        int result;
        const char *argv[] = {
                "argv0",
                "--oml-log-level", "-2",  // log only errors
                "--oml-config", oml_config_file_path
        };
        int argc = (sizeof(argv) / sizeof(char *));

        result = omlc_init("control_node_measures", &argc, argv, NULL);
        if (result == -1) {
                PRINT_ERROR("omlc_init failed: %d\n", result);
                return result;
        }

        mp_consumption = omlc_add_mp("consumption", measure_point_consumption);
        mp_radio = omlc_add_mp("radio", measure_point_radio);

        result = omlc_start();
        if (result == -1) {
                PRINT_ERROR("omlc_start failed: %d\n", result);
                return result;
        }
        return 0;
}


void oml_measures_consumption()
{
        return;
}

void oml_measures_radio()
{
        return;
}


int oml_measures_stop(void)
{
        omlc_close();
        return 0;
}




