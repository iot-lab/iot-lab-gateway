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
        return -1;
}

