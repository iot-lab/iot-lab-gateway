#include <gtest/gtest.h>

#include <unistd.h>
#include "oml_measures.c"



/* Mock EXTERNAL dependency functions
 * with function definition
 */

#define OML_CONFIG_PATH "utils/oml_measures_config.xml"
#define CONSUMPTION_FILE "/tmp/consumption.oml"
#define RADIO_FILE "/tmp/radio.oml"



TEST(test_oml_measures, init_and_stop)
{
        int ret_init;
        int ret_stop;
        ret_init = oml_measures_init(OML_CONFIG_PATH);
        ret_stop = oml_measures_stop();

        ASSERT_EQ(0, ret_init);
        ASSERT_EQ(0, ret_stop);
        ASSERT_NE(-1, access(CONSUMPTION_FILE, F_OK));
        ASSERT_NE(-1, access(RADIO_FILE, F_OK));

}

TEST(test_oml_measures, init_and_stop_with_measures_print)
{
        int ret_init;
        int ret_stop;
        ret_init = oml_measures_init(OML_CONFIG_PATH);

        ret_stop = oml_measures_stop();

        ASSERT_EQ(0, ret_init);
        ASSERT_EQ(0, ret_stop);

}

