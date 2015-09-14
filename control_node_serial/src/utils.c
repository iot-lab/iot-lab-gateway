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

#include <unistd.h>
#include <string.h>
#include "utils.h"


/*
 * Dictionnaries implementation
 *     str -> uint8_t
 */
int get_val(char *key, struct dict_entry dict[], uint8_t *val)
{
        if (!key)
                return -1;
        size_t i = 0;
        while (dict[i].str != NULL) {
                if (!strcmp(dict[i].str, key)) {
                        *val = dict[i].val;
                        return 0;
                }
                i++;
        }
        *val = 0xFF;
        return -1;
}



int get_key(uint8_t val, struct dict_entry dict[], char **key)
{
        size_t i = 0;
        while (dict[i].str != NULL) {
                if (val == dict[i].val) {
                        *key = dict[i].str;
                        return 0;
                }
                i++;
        }
        *key = NULL;
        return -1;
}

