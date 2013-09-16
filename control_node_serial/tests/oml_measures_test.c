#include <gtest/gtest.h>

#include "mock_fprintf.h"  // include before other includes

#include <unistd.h>
#include <sys/stat.h>

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



TEST(test_oml_measures, init_and_stop)
{
        omlc_init_do_mock = 0;
        omlc_start_do_mock = 0;


        int ret_init;
        int ret_stop;
        ret_init = oml_measures_start(OML_CONFIG_PATH);
        ret_stop = oml_measures_stop();

        ASSERT_EQ(0, ret_init);
        ASSERT_EQ(0, ret_stop);
        ASSERT_NE(-1, access(CONSUMPTION_FILE, F_OK));
        ASSERT_NE(-1, access(RADIO_FILE, F_OK));
        unlink(CONSUMPTION_FILE);
        unlink(RADIO_FILE);


}

TEST(test_oml_measures, init_and_stop_with_measures_print)
{
        omlc_init_do_mock = 0;
        omlc_start_do_mock = 0;

        int ret_init;
        int ret_stop;
        ret_init = oml_measures_start(OML_CONFIG_PATH);

        // add measures
        oml_measures_consumption(42, 69, 12.34, 3.3, 40.72);
        oml_measures_radio(42, 70, -20, 0);
        oml_measures_consumption(43, 69, 12.34, 3.3, 40.72);
        oml_measures_radio(43, 70, -20, 0);

        /* write many values to ensure that oml writes them to disk
         * before calling close
         *
         * On gateways, after close the file are still not written to disk
         * that's why I write a tousand of them
         */
        for (int i = 0; i < 1000; i++) {
                oml_measures_consumption(0, 0, 0.0, 0.0, 0.0);
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


}

TEST(test_oml_measures, init_and_stop_error_cases)
{
        omlc_init_do_mock = 1;
        omlc_start_do_mock = 1;
        int ret_init;
        int ret_stop;

        // error on omlc_init
        omlc_init_mock_ret = -1;
        ret_init = oml_measures_start(OML_CONFIG_PATH);
        ASSERT_EQ(-1, ret_init);

        // error on omlc_start
        omlc_init_do_mock = 0;
        omlc_start_mock_ret = -1;
        ret_init = oml_measures_start(OML_CONFIG_PATH);
        ASSERT_EQ(-1, ret_init);
}
