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

#include <gtest/gtest.h>

#include "mock_fprintf.h"  // include before other includes

#include <unistd.h>
#include <sys/stat.h>
#include <math.h>

#include <oml2/omlc.h>


#define omlc_init omlc_init_mock
#define omlc_start omlc_start_mock
int omlc_init(const char* name, int* argc_ptr, const char** argv, o_log_fn logger);
int omlc_start(void);
#include "oml_measures.c"

#undef omlc_init
#undef omlc_start


int omlc_init_do_mock = 0;
int omlc_init_mock_ret = 0;
int omlc_init_mock(const char* name, int* argc_ptr, const char** argv, o_log_fn logger)
{
    if (omlc_init_do_mock)
        return omlc_init_mock_ret;
    else
        return omlc_init(name, argc_ptr, argv, logger);
}

int omlc_start_do_mock = 0;
int omlc_start_mock_ret = 0;
int omlc_start_mock()
{
    if (omlc_start_do_mock)
        return omlc_start_mock_ret;
    else
        return omlc_start();
}


static int file_size(char *file_path)
{
    struct stat st;
    stat(file_path, &st);
    return st.st_size;
}


/* Mock EXTERNAL dependency functions
 * with function definition
 */

#define OML_CONFIG_PATH "utils/oml_measures_config.xml"
#define CONSUMPTION_FILE "/tmp/consumption.oml"
#define RADIO_FILE "/tmp/radio.oml"
#define EVENT_FILE "/tmp/event.oml"
#define SNIFF_FILE "/tmp/sniffer.oml"



TEST(test_oml_measures, init_and_stop)
{
    omlc_init_do_mock = 0;
    omlc_start_do_mock = 0;


    int ret_init;
    int ret_stop;
    ret_init = oml_measures_start(OML_CONFIG_PATH, 1);
    ret_stop = oml_measures_stop();

    ASSERT_EQ(0, ret_init);
    ASSERT_EQ(0, ret_stop);
    ASSERT_NE(-1, access(CONSUMPTION_FILE, F_OK));
    ASSERT_NE(-1, access(RADIO_FILE, F_OK));
    ASSERT_NE(-1, access(SNIFF_FILE, F_OK));
    ASSERT_NE(-1, access(EVENT_FILE, F_OK));
    unlink(CONSUMPTION_FILE);
    unlink(RADIO_FILE);
    unlink(SNIFF_FILE);
    unlink(EVENT_FILE);


}

TEST(test_oml_measures, init_and_stop_with_measures_print)
{
    omlc_init_do_mock = 0;
    omlc_start_do_mock = 0;

    int ret_init;
    int ret_stop;
    ret_init = oml_measures_start(OML_CONFIG_PATH, 0);

    // add measures
    oml_measures_consumption(42, 69, 12.34, 3.3, 40.72);
    oml_measures_radio(42, 70, 11, -20);
    oml_measures_consumption(43, 69, 12.34, 3.3, 40.72);
    oml_measures_radio(43, 70, 26, -20);
    oml_measures_sniffer(42, 0,  11, 1, -91, 255, 42);
    oml_measures_event(42, 0,    65535, "test");
    oml_measures_event(42, 0,    65535, NULL);
    oml_measures_event(42, 0,    65535, "");


    /* write many values to ensure that oml writes them to disk
     * before calling close
     *
     * On gateways, after closing, the files are still not written to disk
     * that's why I write a thousand of them
     */
    for (int i = 0; i < 10000; i++) {
        oml_measures_consumption(0, 0, 0.0, NAN, 0.0);
        oml_measures_radio(0, 0, 0, 0);
    }

    ret_stop = oml_measures_stop();

    ASSERT_EQ(0, ret_init);
    ASSERT_EQ(0, ret_stop);
    // file not empty
    ASSERT_NE(0, file_size(CONSUMPTION_FILE));
    ASSERT_NE(0, file_size(RADIO_FILE));

    unlink(CONSUMPTION_FILE);
    unlink(RADIO_FILE);
    unlink(SNIFF_FILE);
    unlink(EVENT_FILE);
}

TEST(test_oml_measures, init_and_stop_without_oml_and_print_measures)
{
    omlc_init_do_mock = 0;
    omlc_start_do_mock = 1;

    int ret_init;
    int ret_stop;
    ret_init = oml_measures_start(NULL, 1);

    // add measures
    oml_measures_consumption(42, 69, 12.34, 3.3, 40.72);
    ASSERT_STREQ(print_buff, "measures_debug: "
            "consumption_measure 42.000069 12.340000 3.300000 40.720000\n");
    oml_measures_radio(42, 70, 11, -20);
    ASSERT_STREQ(print_buff, "measures_debug: "
            "radio_measure 42.000070 11 -20\n");

    oml_measures_sniffer(42, 999999,  11, -91, 255, 1, 42);
    ASSERT_STREQ(print_buff, "measures_debug: "
            "sniffer 42.999999 11 -91 255 crc_ok 42\n");
    oml_measures_sniffer(42, 999999,  11, -91, 255, 0, 0);
    ASSERT_STREQ(print_buff, "measures_debug: "
            "sniffer 42.999999 11 -91 255 crc_error 0\n");

    oml_measures_event(43, 0, 4, NULL);
    ASSERT_STREQ(print_buff, "measures_debug: event 43.000000 4 (null)\n");
    oml_measures_event(43, 0, 65535, "test");
    ASSERT_STREQ(print_buff, "measures_debug: event 43.000000 65535 test\n");

    ret_stop = oml_measures_stop();

    ASSERT_EQ(0, ret_init);
    ASSERT_EQ(0, ret_stop);
}


TEST(test_oml_measures, init_and_stop_error_cases)
{
    omlc_init_do_mock = 1;
    omlc_start_do_mock = 1;
    int ret_init;
    int ret_stop;

    // error on omlc_init
    omlc_init_mock_ret = -1;
    ret_init = oml_measures_start(OML_CONFIG_PATH, 0);
    ASSERT_EQ(-1, ret_init);
    omlc_start();

    // error on omlc_start
    omlc_init_do_mock = 0;
    omlc_start_mock_ret = -1;
    ret_init = oml_measures_start(OML_CONFIG_PATH, 0);
    ASSERT_EQ(-1, ret_init);
}
