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

#ifndef UTILS_H
#define UTILS_H


#include <stdint.h>

/*
 * Dictionnaries implementation
 *     str -> uint8_t
 *
 *     * Values and keys should be unique.
 *     * Dict should be NULL terminated
 *

struct dict_entry example_d[] = {
        {"key1", val1},
        {"key2", val2},
        {"key3", val3},
        {NULL, 0},
};

 *
 */



struct dict_entry {
        char *str;
        unsigned char val;
};

int get_val(char *key, struct dict_entry dict[], uint8_t *val);
int get_key(uint8_t val, struct dict_entry dict[], char **key);

#endif // UTILS_H
