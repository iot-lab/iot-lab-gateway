#ifndef PROTOCOL_H
#define PROTOCOL_H

#include "constants.h"

struct dict_entry {
        char *str;
        unsigned char val;
};

struct dict_entry periods_d[] = {
        {"140us",  PERIOD_140us},
        {"204us",  PERIOD_204us},
        {"332us",  PERIOD_332us},
        {"588us",  PERIOD_588us},
        {"1100us", PERIOD_1100us},
        {"2116us", PERIOD_2116us},
        {"4156us", PERIOD_4156us},
        {"8244us", PERIOD_8244us},
};

struct dict_entry average_d[] = {
        {"1",    AVERAGE_1},
        {"4",    AVERAGE_4},
        {"16",   AVERAGE_16},
        {"64",   AVERAGE_64},
        {"128",  AVERAGE_128},
        {"256",  AVERAGE_256},
        {"512",  AVERAGE_512},
        {"1024", AVERAGE_1024},
};

struct dict_entry power_source_d[] = {
        {"3.3V",  SOURCE_3_3V},
        {"5V",    SOURCE_5V},
        {"BATT",  SOURCE_BATT},
};

#endif // PROTOCOL_H
