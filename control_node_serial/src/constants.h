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

#ifndef CONSTANTS_H
#define CONSTANTS_H

enum defines {
    SYNC_BYTE            = 0x80,
    ASYNC_FRAME_MASK     = 0xF0,
};

// type byte
enum frame_type {
    /* Commands */
    OPEN_NODE_STOP       = 0x10,
    OPEN_NODE_START      = 0x11,

    SET_TIME             = 0x20,
    SET_NODE_ID          = 0x21,

    /* LED management */
    GREEN_LED_ON         = 0x35,
    GREEN_LED_BLINK      = 0x36,


    /* Control node measure/noise config */
    CONFIG_RADIO_STOP    = 0xC0,
    CONFIG_RADIO_MEAS    = 0xC1,
    CONFIG_RADIO_SNIFFER = 0xC3,
    /*
     * CONFIG_RADIO_NOISE   = 0xC2,
     * CONFIG_RADIO_INJECTION = 0xC4,
     *
     * CONFIG_SENSOR        = 0xC9,
     */
    CONFIG_CONSUMPTION   = 0xCC,

    CONFIG_GPIO          = 0xCD,

    /*
     * Asyncronous frames
     */

    // config ACK frame
    ACK_FRAME            = 0xFA,

    // Measures
    RADIO_MEAS_FRAME     = 0xF1,
    RADIO_SNIFFER_FRAME  = 0xF3,
    CONSUMPTION_FRAME    = 0xFC,
    EVENT_FRAME          = 0xFE,

    LOGGER_FRAME         = 0xEE,  // log messages

    /*
     * Test commands
     */
    TEST_GPIO            = 0x71,
    TEST_I2C2            = 0x72,
    TEST_RADIO_PING_PONG = 0x73,

    TEST_PPS             = 0x74,
    TEST_GOT_PPS         = 0x76,
};

enum ack_nack {
    ACK  = 0xA,
    NACK = 0x2,
};

enum alimentation {
    BATTERY      = 0x0,
    DC_CHARGE    = 0x1,
    DC_NO_CHARGE = 0x2,
};

enum mode {
    STOP  = 0x0,
    START = 0x1,
};


/* consumption config */
enum power_measures {
    MEASURE_POWER       = 1 << 0,
    MEASURE_VOLTAGE     = 1 << 1,
    MEASURE_CURRENT     = 1 << 2,
    // Nothing on bit 4
    PW_SRC_3_3V         = 1 << 4,
    PW_SRC_5V           = 1 << 5,
    PW_SRC_BATT         = 1 << 6,
    PW_SRC_MASK = 0x70,
};

// INA226 config
enum ina226_periods {
    PERIOD_140us  = 0,
    PERIOD_204us  = 1,
    PERIOD_332us  = 2,
    PERIOD_588us  = 3,
    PERIOD_1100us = 4,
    PERIOD_2116us = 5,
    PERIOD_4156us = 6,
    PERIOD_8244us = 7,

    PERIOD_MASK  = 0x7,
};
// Padding between period and average: 0 << 3
enum ina226_average {
    AVERAGE_1     = 0 << 4,
    AVERAGE_4     = 1 << 4,
    AVERAGE_16    = 2 << 4,
    AVERAGE_64    = 3 << 4,
    AVERAGE_128   = 4 << 4,
    AVERAGE_256   = 5 << 4,
    AVERAGE_512   = 6 << 4,
    AVERAGE_1024  = 7 << 4,

    AVERAGE_MASK = 0x70,
};

/*
 * Radio config
 *     Extracted from phy.h
 *     Only values starting with POWER are used and valid
 */
enum radio_tx_power {
    UNUSED_PHY_POWER_m30dBm,
    UNUSED_PHY_POWER_m29dBm,
    UNUSED_PHY_POWER_m28dBm,
    UNUSED_PHY_POWER_m27dBm,
    UNUSED_PHY_POWER_m26dBm,
    UNUSED_PHY_POWER_m25dBm,
    UNUSED_PHY_POWER_m24dBm,
    UNUSED_PHY_POWER_m23dBm,
    UNUSED_PHY_POWER_m22dBm,
    UNUSED_PHY_POWER_m21dBm,
    UNUSED_PHY_POWER_m20dBm,
    UNUSED_PHY_POWER_m19dBm,
    UNUSED_PHY_POWER_m18dBm,
    POWER_m17dBm,
    UNUSED_PHY_POWER_m16dBm,
    UNUSED_PHY_POWER_m15dBm,
    UNUSED_PHY_POWER_m14dBm,
    UNUSED_PHY_POWER_m13dBm,
    POWER_m12dBm,
    UNUSED_PHY_POWER_m11dBm,
    UNUSED_PHY_POWER_m10dBm,
    POWER_m9dBm,
    UNUSED_PHY_POWER_m8dBm,
    POWER_m7dBm,
    UNUSED_PHY_POWER_m6dBm,
    POWER_m5dBm,
    POWER_m4dBm,
    POWER_m3dBm,
    POWER_m2dBm,
    POWER_m1dBm,
    POWER_0dBm,
    POWER_0_7dBm,
    UNUSED_PHY_POWER_1dBm,
    POWER_1_3dBm,
    POWER_1_8dBm,
    UNUSED_PHY_POWER_2dBm,
    POWER_2_3dBm,
    POWER_2_8dBm,
    POWER_3dBm,
    UNUSED_PHY_POWER_4dBm,
    UNUSED_PHY_POWER_5dBm,
};


/* logger level, copied from python logger ones */
enum cn_logger_levels {
    LOGGER_CRITICAL = 50,
    LOGGER_ERROR    = 40,
    LOGGER_WARNING  = 30,
    LOGGER_INFO     = 20,
    LOGGER_DEBUG    = 10,
    LOGGER_NOTSET   = 0,
};

#endif // CONSTANTS_H
