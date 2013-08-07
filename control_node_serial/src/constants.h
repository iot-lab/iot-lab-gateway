#ifndef CONSTANTS_H
#define CONSTANTS_H

enum defines {
        SYNC_BYTE           = 0x80,
        MEASURES_FRAME_MASK = 0xF0,
        TIME_FACTOR         = 32768,
};

// type byte
enum frame_type {
        // Commands
	OPEN_NODE_START    = 0x70,
	OPEN_NODE_STOP     = 0x71,

	RESET_TIME         = 0x72,

        // Measure config
	CONFIG_RADIO       = 0x74,
	CONFIG_RADIO_POLL  = 0x75,
	CONFIG_RADIO_NOISE = 0x76,
	CONFIG_SNIFFER     = 0x77,

	CONFIG_SENSOR      = 0x78,

	CONFIG_POWER_POLL  = 0x79,

        // Error
	ERROR_FRAME        = 0xEE,

        // Command ack for measures handler
        ACK_FRAME          = 0xFA,

        // Measures
	RADIO_POLL_FRAME   = 0xFE,
	PW_POLL_FRAME      = 0xFF,
};

enum ack_nack {
        ACK  = 0xA,
        NACK = 0x2,
};

enum alimentation {
	BATTERY = 0x0,
        DC      = 0x1,
};

enum radio_config {
        RADIO_STOP = 0x0,
        RADIO_START = 0x1,
};

enum cn_error_t {
	OK                         = 0,
        NETWORK_QUEUE_OVERFLOW     = -1,
        APPLICATION_QUEUE_OVERFLOW = -2,
	DEFENSIVE                  = -3,
};

/* consumption config */
// Wanted Measures
enum power_measures {
        MEASURE_POWER       = 1 << 0,
        MEASURE_VOLTAGE     = 1 << 1,
        MEASURE_CURRENT     = 1 << 2,
        // Nothing on bit 4
        SOURCE_3_3V         = 1 << 4,
        SOURCE_5V           = 1 << 5,
        SOURCE_BATT         = 1 << 6,

        CONSUMPTION_START   = 1 << 7,
        CONSUMPTION_STOP    = 0 << 7,
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
};

// Radio config
//TODO review still correct on next openlab release
enum radio_tx_power {
        POWER_3dBm   = 38,
        POWER_2_8dBm = 37,
        POWER_2_3dBm = 36,
        POWER_1_8dBm = 34,
        POWER_1_3dBm = 33,
        POWER_0_7dBm = 31,
        POWER_0dBm   = 30,
        POWER_m1dBm  = 29,
        POWER_m2dBm  = 28,
        POWER_m3dBm  = 27,
        POWER_m4dBm  = 26,
        POWER_m5dBm  = 25,
        POWER_m7dBm  = 23,
        POWER_m9dBm  = 21,
        POWER_m12dBm = 18,
        POWER_m17dBm = 13,
};

#endif // CONSTANTS_H
