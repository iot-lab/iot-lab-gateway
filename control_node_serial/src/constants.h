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
enum radio_tx_power {
        POWER_3dBm   = 0x0,
        POWER_2_8dBm = 0x1,
        POWER_2_3dBm = 0x2,
        POWER_1_8dBm = 0x3,
        POWER_1_3dBm = 0x4,
        POWER_0_7dBm = 0x5,
        POWER_0dBm   = 0x6,
        POWER_m1dBm  = 0x7,
        POWER_m2dBm  = 0x8,
        POWER_m3dBm  = 0x9,
        POWER_m4dBm  = 0xA,
        POWER_m5dBm  = 0xB,
        POWER_m7dBm  = 0xC,
        POWER_m9dBm  = 0xD,
        POWER_m12dBm = 0xE,
        POWER_m17dBm = 0xF,
};
enum radio_channel {
        CHANNEL_11 = 0x0 << 4,
        CHANNEL_12 = 0x1 << 4,
        CHANNEL_13 = 0x2 << 4,
        CHANNEL_14 = 0x3 << 4,
        CHANNEL_15 = 0x4 << 4,
        CHANNEL_16 = 0x5 << 4,
        CHANNEL_17 = 0x6 << 4,
        CHANNEL_18 = 0x7 << 4,
        CHANNEL_19 = 0x8 << 4,
        CHANNEL_20 = 0x9 << 4,
        CHANNEL_21 = 0xA << 4,
        CHANNEL_22 = 0xB << 4,
        CHANNEL_23 = 0xC << 4,
        CHANNEL_24 = 0xD << 4,
        CHANNEL_25 = 0xE << 4,
        CHANNEL_26 = 0xF << 4,
};

#endif // CONSTANTS_H
